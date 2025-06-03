from django import forms

from order.models import Order, ReturnProduct, OrderItem
from shop.models import Product


class CreateOrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['name', 'phone', 'address']


class ReturnOrderForm(forms.Form):
    return_products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='کدام کالا(ها) را میخواهید مرجوع کنید:'
    )

    def __init__(self, *args, **kwargs):
        custom_queryset = kwargs.pop('custom_queryset', None)
        super(ReturnOrderForm, self).__init__(*args, **kwargs)

        if custom_queryset:
            self.fields['return_products'].queryset = custom_queryset
            self.fields['return_products'].widget.choices = [(p.product.pk, p.__str__()) for p in custom_queryset]


