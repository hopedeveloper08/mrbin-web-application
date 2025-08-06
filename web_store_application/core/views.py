from django.views.generic import (
    ListView,
    FormView,
    TemplateView,
)
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from urllib.parse import unquote
from zarinpal import ZarinPal
from utils.Config import Config

from django.http import FileResponse
from rembg import remove
from io import BytesIO

from .models import Bin, Order, OrderItem
from .forms import CustomerInfoForm
from .local_config import MERCHANT_ID, NESHAN_KEY
from .filters import BinFilter
from .postage_price import get_postage_price

import requests


ZARINPAL = ZarinPal(Config(merchant_id= MERCHANT_ID))


class MainPage(ListView):
    model = Bin
    template_name = 'main/main.html'  
    context_object_name = 'bins'
    paginate_by = 3

    def get_queryset(self):
        bins = Bin.objects.order_by('title')
        self.bin_filter = BinFilter(self.request.GET, queryset=bins)
        return self.bin_filter.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.bin_filter
        return context


class OrderPage(FormView):
    template_name = 'order/order.html'
    form_class = CustomerInfoForm
    success_url = '/order/success/'

    def dispatch(self, request, *args, **kwargs):
        if request.session.get('postage', None) is None:
            return redirect('/address/')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):

        # calculate total price
        cart = self.request.session.get('cart', {})
        total_price = 0
        items = []
        for title, qty in cart.items():
            try:
                bin = Bin.objects.get(title=title)
            except Bin.DoesNotExist:
                continue
            total_price += int(bin.price) * qty
            items.append((bin, qty))
        total_price += self.request.session['postage']

        # initiate payment
        response = ZARINPAL.payments.create({
            "amount": total_price,
            "currency": 'IRT',
            "callback_url": 'https://mr-bin.ir/order-registration/',
            "description": 'Transaction for bin.',
            'mobile': form.instance.phone_number,
            'order_id': form.instance.customer_name,
        })
        if "data" in response and "authority" in response["data"]:
            self.request.session['customer_name'] = form.instance.customer_name
            self.request.session['phone_number'] = form.instance.phone_number
            self.request.session['postal_code'] = form.instance.postal_code
            self.request.session['total_price'] = total_price
            payment_url = ZARINPAL.payments.generate_payment_url(response["data"]["authority"])
            return redirect(payment_url)
        else:
            messages.error(self.request, 'ارتباط با درگاه پرداخت برقرار نشد.')
            return redirect('/')


class Address(TemplateView):
    template_name = 'address/address.html'


def order_registration(request):

    # verify payment
    if request.GET.get('Status') != "OK":
        messages.error(request, 'پرداخت ناموفق بود.')
        return redirect('/')
    response = ZARINPAL.verifications.verify({
        "amount": request.session['total_price'],
        "authority": request.GET.get('Authority'),
    })
    if response["data"]["code"] != 100 and response["data"]["code"] != 101:
        messages.error(request, f'پرداخت ناموفق بود. کد خطا: {response["data"]["code"]}')
        return redirect('/')

    # create order
    order = Order.objects.create(
        customer_name=request.session['customer_name'],
        phone_number=request.session['phone_number'],
        address=request.session['address'],
        lng=request.session['lng'],
        lat=request.session['lat'],
        postal_code=request.session['postal_code'],
        total_price=request.session['total_price'],
    )

    # order items
    cart = request.session.get('cart', {})
    for title, qty in cart.items():
        bin = Bin.objects.get(title=title)
        if bin.inventory - qty < 0:
            bin.inventory = 0
        else:
            bin.inventory -= qty
        bin.save()
        OrderItem.objects.create(order=order, bin=bin, quantity=qty)

    # clear cart
    request.session['cart'] = {}
    request.session['order_id'] = order.id
    
    return redirect('/order/success/')


class OrderSuccessView(TemplateView):
    template_name = 'order/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.get('order_id')
        context['order'] = Order.objects.get(id=order_id) if order_id else None
        return context
    

def add_to_cart(request, title):
    title = unquote(title)
    
    # if exist 
    try:
        bin = Bin.objects.get(title=title)
    except Bin.DoesNotExist:
        messages.error(request, f'"{title}" یافت نشد.')
        return redirect('/')
    
    # load cart
    cart = request.session.get('cart', {})
    count = cart.get(title, 0)

    # add to cart if enough inventory
    if count < bin.inventory:
        cart[title] = count + 1
        request.session['cart'] = cart
        messages.success(request, f'یک "{title}" به سبد خرید اضافه شد')
    else:
        messages.error(request, f'موجودی "{title}" کافی نیست')

    # Back to bin
    referer = request.META.get('HTTP_REFERER', reverse('main'))
    return HttpResponseRedirect(referer)


def remove_from_cart(request, title):
    title = unquote(title)

    # if exist 
    try:
        Bin.objects.get(title=title)
    except Bin.DoesNotExist:
        messages.error(request, f'"{title}" یافت نشد.')
        return redirect('/')
    
    # if not in cart 
    cart = request.session.get('cart', {})
    if title not in cart:
        return HttpResponse(status=204)
    
    # remove a bin
    cart[title] -= 1
    
    # remove if bin not in cart
    if cart[title] == 0:
        del cart[title]

    # confirmation
    request.session['cart'] = cart
    messages.error(request, f'یک "{title}" از سبد خرید حذف شد')

    # Back to bin
    referer = request.META.get('HTTP_REFERER', reverse('main'))
    return HttpResponseRedirect(referer)


def calculate_postage(request):
    lat = request.GET.get('lat', '')
    lng = request.GET.get('lng', '')
    address = request.GET.get('address', '')
    address = unquote(address)
    
    # out of shiraz
    if address == 'خارج از شیراز' or address == 'تحویل درب فروشگاه':
        request.session['lat'] = 0
        request.session['lng'] = 0
        request.session['postage'] = 0
        request.session['address'] = address
        return redirect('/order')

    # validation
    if lat == '' or lng == '' or address == '':
        return HttpResponse(status=204)
    lat = float(lat)
    lng = float(lng)

    # get postage
    request.session['postage'] = get_postage_price(lat, lng, request.session.get('cart'))
    
    # set address
    request.session['lat'] = lat
    request.session['lng'] = lng
    request.session['address'] = address
    
    return redirect('/order')


@csrf_exempt
def reverse_geocode(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    if not lat or not lng:
        return JsonResponse({'error': 'lat/lng required'}, status=400)

    headers = {
        'Api-Key': NESHAN_KEY
    }
    url = f'https://api.neshan.org/v5/reverse?lat={lat}&lng={lng}'
    try:
        res = requests.get(url, headers=headers)
        return JsonResponse(res.json(), status=res.status_code)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
def remove_bg(request):
    if request.method == 'GET':
        return render(request, 'service/remove_bg.html')
    
    if request.method == 'POST' and request.FILES.get('image'):
        img_file = request.FILES['image']
        input_bytes = img_file.read()
        output_bytes = remove(input_bytes)

        buffer = BytesIO(output_bytes)
        return FileResponse(buffer, as_attachment=True, filename='no_bg.png')

    return render(request, 'service/remove_bg.html')


@staff_member_required
def location(request):
    if request.method == 'GET':
        return render(request, 'service/location.html')
    
    if request.method == "POST":
        order_id = request.POST.get("order_id")
        print(order_id)
        try:
            order = Order.objects.get(id=order_id)
            return JsonResponse({"lat": order.lat, "lng": order.lng})
        except Order.DoesNotExist:
            return JsonResponse({"error": "شماره سفارش وجود ندارد!"}, status=404)
