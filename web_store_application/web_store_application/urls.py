from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    MainPage,
    OrderPage,
    OrderSuccessView,
    add_to_cart,
    remove_from_cart
)


urlpatterns = [
    path('admin/', admin.site.urls),

    # core
    path('', MainPage.as_view(), name='main'),
    path('order/', OrderPage.as_view(), name='order'),
    path('order/success/', OrderSuccessView.as_view(), name='order_success'),
    path('add-to-cart/<str:title>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<str:title>/', remove_from_cart, name='remove-from-cart'),
] 


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
