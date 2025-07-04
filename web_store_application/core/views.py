from django.views.generic import (
    ListView,
    FormView,
    TemplateView,
)
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

from urllib.parse import unquote
from zarinpal import ZarinPal
from utils.Config import Config

from .models import Bin, Order, OrderItem
from .forms import CustomerInfoForm
from .local_config import POSTAGE, MERCHANT_ID


ZARINPAL = ZarinPal(Config(merchant_id= MERCHANT_ID))


class MainPage(ListView):
    model = Bin
    template_name = 'main/main.html'  
    context_object_name = 'bins'
    paginate_by = 6

    def get_queryset(self):
        return Bin.objects.order_by('title')


class OrderPage(FormView):
    template_name = 'order/order.html'
    form_class = CustomerInfoForm
    success_url = '/order/success/'

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
        total_price += POSTAGE

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
            self.request.session['user_info'] = {
                'customer_name': form.instance.customer_name,
                'phone_number': form.instance.phone_number,
                'address': form.instance.address,
                'postal_code': form.instance.postal_code,
                'total_price': total_price,
            }
            payment_url = ZARINPAL.payments.generate_payment_url(response["data"]["authority"])
            return redirect(payment_url)
        else:
            messages.error(self.request, 'ارتباط با درگاه پرداخت برقرار نشد.')
            return redirect('/')


def order_registration(request):

    # verify payment
    if request.GET.get('Status') != "OK":
        messages.error(request, 'پرداخت ناموفق بود.')
        return redirect('/')
    response = ZARINPAL.verifications.verify({
        "amount": request.session['user_info']['total_price'],
        "authority": request.GET.get('Authority'),
    })
    if response["data"]["code"] != 100 and response["data"]["code"] != 101:
        messages.error(request, f'پرداخت ناموفق بود. کد خطا: {response["data"]["code"]}')
        return redirect('/')

    # create order
    user_info = request.session['user_info']
    order = Order.objects.create(
        customer_name=user_info['customer_name'],
        phone_number=user_info['phone_number'],
        address=user_info['address'],
        postal_code=user_info['postal_code'],
        total_price=user_info['total_price'],
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
