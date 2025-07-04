from django.contrib import admin
from django.contrib.auth.models import Group, User

import jdatetime
from django.utils.timezone import localtime

from .models import Bin, Order, OrderItem


admin.site.site_header = "پنل مدیریت آقای سطل"
admin.site.site_title = "آقای سطل"
admin.site.index_title = "مدیریت سایت"

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'size', 'color', 'inventory', 'price']
    search_fields = ['title', 'brand']
    list_filter = ['brand', 'color', 'size']
    ordering = ['brand', 'size']
    list_editable = ['inventory', 'price']
    fieldsets = (
        (None, {
            'fields': ('title', 'brand', 'size', 'color', 'price', 'inventory', 'dimensions', 'image')
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1  
    fields = ['bin', 'quantity']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    def created_at_jalali(self, obj):
        local_dt = localtime(obj.created_at)  
        jdt = jdatetime.datetime.fromgregorian(datetime=local_dt)
        return jdt.strftime('%Y/%m/%d %H:%M')
    created_at_jalali.short_description = 'زمان ایجاد'
    
    list_display = ['id', 'customer_name', 'phone_number', 'status', 'formatted_price', 'created_at_jalali']
    list_display_links = ['id', 'customer_name', 'phone_number']
    list_filter = ['status', 'created_at']
    search_fields = ['customer_name', 'phone_number']
    ordering = ['-created_at']
    inlines = [OrderItemInline]
    list_editable = ['status']
    readonly_fields = ['created_at_jalali', 'formatted_price']

    fieldsets = (
        ('اطلاعات مشتری', {
            'fields': ('customer_name', 'phone_number', 'address', 'postal_code')
        }),
        ('اطلاعات سفارش', {
            'fields': ('status', 'formatted_price', 'created_at_jalali')
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        self.update_order_total(form.instance)

    def update_order_total(self, order):
        total = sum(item.quantity * item.bin.price for item in order.items.all())
        order.total_price = total
        order.save()
