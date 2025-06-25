from django.views.generic import (
    ListView,
    FormView,
    TemplateView,
)
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse

from .models import Bin, Order, OrderItem
from .forms import CustomerInfoForm


class MainPage(ListView):
    model = Bin
    template_name = 'main/main.html'  
    context_object_name = 'bins'
    paginate_by = 6


class OrderPage(FormView):
    template_name = 'order/order.html'
    form_class = CustomerInfoForm
    success_url = 'success'

    def form_valid(self, form):

        # postage
        postage = 79_000
        
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
        total_price += postage

        # payment
        
        # create order
        order = form.save(commit=False)
        order.total_price = total_price
        order.save()

        # order items and reduce inventory
        for bin, qty in items:
            if bin.inventory - qty < 0:
                bin.inventory = 0
            else:
                bin.inventory -= qty
            bin.save()
            OrderItem.objects.create(order=order, bin=bin, quantity=qty)

        # clear cart
        self.request.session['cart'] = {}
        self.request.session['order_id'] = order.id
        
        return redirect('order_success')


class OrderSuccessView(TemplateView):
    template_name = 'order/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.request.session.get('order_id')
        context['order'] = Order.objects.get(id=order_id) if order_id else None
        return context
    

def add_to_cart(request, title):

    # if exist 
    try:
        bin = Bin.objects.get(title=title)
    except Bin.DoesNotExist:
        return redirect('main')
    
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
    
    # if exist 
    try:
        Bin.objects.get(title=title)
    except Bin.DoesNotExist:
        return redirect('main')
    
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
