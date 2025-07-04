from .models import Bin
from .local_config import POSTAGE

def formatted_price(price):
    return f'{price:,}'


def cart_contents(request):
    cart = request.session.get('cart', {})
    
    products_in_cart = []
    total_price = 0
    for title, quantity in cart.items():
        try:
            bin = Bin.objects.get(title=title)
            products_in_cart.append({
                'title': bin.title,
                'quantity': quantity,
                'price': formatted_price(int(bin.price)),
                'total_price': formatted_price(int(bin.price) * quantity),
                'image': bin.image,
            })
            total_price += int(bin.price) * quantity
        except Bin.DoesNotExist:
            continue
    
    return {
        'cart_items_count': sum(list(map(lambda x: x[1], cart.items()))),
        'cart_items': products_in_cart,
        'total_price': formatted_price(total_price),
        'postage': formatted_price(POSTAGE),
        'total_price_with_postage': formatted_price(total_price + POSTAGE),
    }
