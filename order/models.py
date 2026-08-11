from shop.models import Product, DiscountCode
from django.db import models
from django.conf import settings
User = settings.AUTH_USER_MODEL
from django_jalali.db import models as jmodels
from shop.models import Image

# Create your models here.


class Order(models.Model):
    order_status_choices = (
        ('در صف بررسی', 'در صف بررسی'),
        ('تایید سفارش', 'تایید سفارش'),
        ('دریافت از فروشنده', 'دریافت از فروشنده'),
        ('آماده سازی سفارش', 'آماده سازی سفارش'),
        ('تحویل به پست', 'تحویل به پست'),
        ('تحویل مرسوله به مشتری', 'تحویل مرسوله به مشتری'),
        ('عودت هزینه به دلیل عدم موجودی', 'عودت هزینه به دلیل عدم موجودی'),
        ('لغو شده', 'لغو شده'),
    )
    status = models.CharField(choices=order_status_choices, verbose_name='وضعیت', default='در صف بررسی', max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', verbose_name='کاربر')
    name = models.CharField(max_length=120, verbose_name='نام تحویل گیرنده')
    address = models.CharField(max_length=150, verbose_name='آدرس')
    phone = models.CharField(max_length=11, verbose_name='شماره تلفن تحویل گیرنده')
    created = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = models.DateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')
    final_cost = models.PositiveIntegerField(default=0, verbose_name='مبلغ قابل پرداخت نهایی (با احتساب کد تخفیف)')
    paid = models.BooleanField(default=False, verbose_name='پرداخت با موفقیت')
    discount_code = models.ForeignKey(DiscountCode, verbose_name='کد تخفیف اعمال شده', on_delete=models.CASCADE, null=True, blank=True)
    delivery_time = models.DateTimeField(verbose_name='زمان تحویل مرسوله به مشتری', null=True, blank=True)

    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_total_weight(self):
        return sum(item.get_weight() for item in self.items.all())

    def get_post_cost(self):
        total_weight = self.get_total_weight()
        if total_weight == 0:
            return 0
        elif 0 < total_weight < 1000:
            return 20000
        elif 1000 <= total_weight <= 20000:
            return 30000
        elif total_weight > 2000:
            return 50000

    def get_final_cost(self):
        return self.get_total_cost() + self.get_post_cost()

    def __str__(self):
        return f"order {self.id}"

    class Meta:
        ordering = ['-created']
        verbose_name = 'سفارش'
        verbose_name_plural = 'سفارشات'
        indexes = [
            models.Index(fields=['created']),
        ]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='orders')
    size = models.CharField(max_length=25, null=True, blank=True, verbose_name='اندازه')
    color = models.CharField(max_length=25, null=True, blank=True, verbose_name='رنگ')
    price = models.PositiveIntegerField(default=0, verbose_name='قیمت')
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد')
    weight = models.PositiveIntegerField(default=0, verbose_name='وزن')

    def __str__(self):
        temp = f"{self.product.name}"
        if self.size:
            temp += f" ({self.size})"
        if self.color:
            temp += f" ({self.color})"
        return temp

    def get_cost(self):
        return self.price * self.quantity

    def get_weight(self):
        return self.weight * self.quantity


class ReturnOrder(models.Model):
    order = models.ForeignKey(Order, related_name='return_products', on_delete=models.CASCADE)
    cost = models.CharField(default='', max_length=7, verbose_name='مبلغ قابل بازگشت به خریدار')
    accepted = models.BooleanField(default=False, verbose_name='پذیرش مرجوعی')
    created = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')

    def total_cost(self):
        return sum(
            item.product.off_price * item.quantity
            for item in self.return_products.all()
        )

    class Meta:
        ordering = ['created']
        verbose_name = 'سفارش مرجوعی'
        verbose_name_plural = 'سفارشات مرجوعی'


class ReturnProduct(models.Model):
    return_order = models.ForeignKey(ReturnOrder, related_name='return_products', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='returns', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, verbose_name='تعداد مرجوعی')
    explanation = models.TextField(default='', verbose_name='توضیحات مرجوعی')
    photo = models.ImageField(upload_to='return_products/', verbose_name='تصویر کالای مرجوعی')



