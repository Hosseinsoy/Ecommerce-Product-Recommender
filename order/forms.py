from django import forms

from order.models import Order, ReturnProduct, OrderItem
from shop.models import Product


class CreateOrderForm(forms.ModelForm):
    address = forms.CharField(
        widget=forms.HiddenInput(attrs={
            "id": "id_address"
        })
    )

    class Meta:
        model = Order
        fields = ['name', 'phone', 'address']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'نام و نام خانوادگی تحویل گیرنده'
        })

        self.fields['phone'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'شماره تلفن تحویل گیرنده'
        })


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
