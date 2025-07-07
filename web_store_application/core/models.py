from django.db import models
from django.utils.text import slugify


class Bin(models.Model):
    title = models.CharField(max_length=128, verbose_name='عنوان')
    slug = models.SlugField(unique=True, blank=True)
    inventory = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    brand = models.CharField(max_length=128, verbose_name='برند')
    size = models.PositiveIntegerField(verbose_name='سایز')
    color = models.CharField(max_length=32, verbose_name='رنگ')
    price = models.PositiveIntegerField(verbose_name='قیمت')
    dimensions = models.CharField(max_length=16, blank=True, default='', verbose_name='ابعاد')
    image = models.ImageField(upload_to='products/', verbose_name='عکس')
    create_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    class Meta:
        verbose_name = 'سطل'
        verbose_name_plural = 'سطل'

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @property
    def formatted_price(self):
        return f"{self.price:,}"
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('p', 'در انتظار'),
        ('s', 'ارسال شده'),
    ]

    customer_name = models.CharField(max_length=32, verbose_name='نام مشتری')
    phone_number = models.CharField(max_length=11, verbose_name='شماره تلفن')
    address = models.TextField(verbose_name='آدرس')
    postal_code = models.CharField(max_length=32, verbose_name='کد پستی')
    lng = models.FloatField(verbose_name='طول جغرافیایی')
    lat = models.FloatField(verbose_name='عرض جغرافیایی')
    total_price = models.PositiveIntegerField(default=0, verbose_name='قیمت کل')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='p', verbose_name='وضعیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ایجاد', editable=False)

    class Meta:
        verbose_name = 'سفارشات'
        verbose_name_plural = 'سفارشات'
    
    def __str__(self):
        return f"#{self.id} - {self.customer_name}"
    
    @property
    def formatted_price(self):
        return f"{self.total_price:,}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name='سفارش')
    bin = models.ForeignKey(Bin, on_delete=models.PROTECT, verbose_name='سطل')
    quantity = models.PositiveIntegerField(verbose_name='تعداد')

    def __str__(self):
        return f"{self.quantity} x {self.bin.title}"


class PostagePrice(models.Model):
    init = models.PositiveIntegerField(verbose_name='قیمت اولیه')
    per_km = models.PositiveIntegerField(verbose_name='قیمت به ازای هر کیلومتر')

    class Meta:
        verbose_name = 'هزینه پست'
        verbose_name_plural = 'هزینه پست'
    
    def __str__(self):
        return f"قیمت اولیه: {self.init}, قیمت به ازای هر کیلومتر: {self.per_km}"
