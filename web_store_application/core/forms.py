from django.forms import ModelForm

from .models import Order


class CustomerInfoForm(ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'phone_number', 'postal_code'] 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control shadow-sm'})
            