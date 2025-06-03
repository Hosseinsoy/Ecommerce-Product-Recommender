import django_filters
from .models import Product, Category

import django_filters


class ProductFilter(django_filters.FilterSet):
    SORT_CHOICES = (
        ('newest', 'جدیدترین'),
        ('cheapest', 'ارزان ترین'),
        ('expensive', 'گران ترین'),
    )

    ordering = django_filters.ChoiceFilter(
        label='مرتب سازی براساس',
        choices=SORT_CHOICES,
        method='filter_by_order'
    )

    # Correct field name should be 'off_price'
    price = django_filters.RangeFilter(field_name='off_price', label='محدوده قیمت')

    class Meta:
        model = Product
        fields = {
            'category': ['exact'],
            'off_price': ['exact'],  # Optional: To ensure this field is in the filterset
        }

    def filter_by_order(self, queryset, name, value):
        if value == 'newest':
            return queryset.order_by('-created')
        elif value == 'cheapest':
            return queryset.order_by('off_price')
        elif value == 'expensive':
            return queryset.order_by('-off_price')
        return queryset