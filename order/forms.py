from django import forms

from order.models import Order, ReturnProduct, OrderItem
from shop.models import Product


class CreateOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'phone', 'address']


class ReturnOrderForm(forms.Form):

    return_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='کدام کالا(ها) را میخواهید مرجوع کنید:'
    )

    def __init__(self, *args, **kwargs):

        custom_queryset = kwargs.pop(
            'custom_queryset',
            None
        )

        super().__init__(*args, **kwargs)

        if custom_queryset is not None:

            # اگر OrderItem فرستاده شده، Productهای آن را استخراج کن
            product_ids = custom_queryset.values_list(
                'product_id',
                flat=True
            )

            self.fields['return_products'].queryset = Product.objects.filter(
                pk__in=product_ids
            )
