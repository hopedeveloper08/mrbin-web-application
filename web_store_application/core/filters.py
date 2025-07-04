import django_filters
from .models import Bin

class BinFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='عنوان')
    brand = django_filters.ChoiceFilter(label='برند')
    color = django_filters.ChoiceFilter(label='رنگ')
    size = django_filters.ChoiceFilter(label='سایز')

    class Meta:
        model = Bin
        fields = ['title', 'brand', 'color', 'size']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['brand'].extra['choices'] = self.filters['brand'].field.choices = self.get_distinct_choices('brand')
        self.filters['color'].extra['choices'] = self.filters['color'].field.choices = self.get_distinct_choices('color')
        self.filters['size'].extra['choices'] = self.filters['size'].field.choices = self.get_distinct_choices('size')

    def get_distinct_choices(self, field_name):
        values = Bin.objects.values_list(field_name, flat=True).distinct()
        return [(val, val) for val in values if val]
