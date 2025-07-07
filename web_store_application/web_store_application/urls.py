from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    MainPage,
    OrderPage,
    OrderSuccessView,
    Address,
    add_to_cart,
    remove_from_cart,
    order_registration,
    calculate_postage,
    reverse_geocode,
)


urlpatterns = [
    # admin
    path('ali/', admin.site.urls),

    # core
    path('', MainPage.as_view(), name='main'),
    path('order/', OrderPage.as_view(), name='order'),
    path('order/success/', OrderSuccessView.as_view(), name='order-success'),
    path('address/', Address.as_view(), name='address'),
    path('add-to-cart/<str:title>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<str:title>/', remove_from_cart, name='remove-from-cart'),
    path('order-registration/', order_registration, name='order-registration'),
    path('calculate-postage/', calculate_postage, name='calculate-postage'),
    path('reverse-geocode/', reverse_geocode),
] 


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
