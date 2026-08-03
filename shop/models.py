from django.db import models
from slugify import slugify as alt_slugify
from django_jalali.db import models as jmodels
from django.urls import reverse


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=250, verbose_name='نام')
    slug = models.SlugField(max_length=250, unique=True)
    image_file = models.ImageField(upload_to='images/%Y/%m/%d', verbose_name='تصویر')

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name'])]
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی ها'

    # def get_absolute_url(self):
    #     return reverse('shop:product_list_by_category', args=[self.slug])

    def __str__(self):
        return self.name


class Product(models.Model):
    seller = models.ForeignKey('account.ShopSeller', default=1, on_delete=models.CASCADE, verbose_name='فروشنده', related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='دسته بندی')
    name = models.CharField(max_length=250, verbose_name='نام')
    description = models.TextField(max_length=1200, verbose_name='توضیحات')
    inventory = models.PositiveIntegerField(default=0, verbose_name='موجودی')
    is_available = models.BooleanField(default=True, verbose_name='موجود می باشد')
    weight = models.PositiveIntegerField(default=0, verbose_name='وزن')
    price = models.PositiveIntegerField(default=0, verbose_name='قیمت')
    off = models.PositiveIntegerField(default=0, verbose_name='درصد تخفیف')
    off_price = models.PositiveIntegerField(default=0, verbose_name='قیمت پس از اعمال تخفیف')
    created = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated = jmodels.jDateTimeField(auto_now=True, verbose_name='تاریخ آپدیت')
    slug = models.SlugField(max_length=250, unique=True)
    has_size_option = models.BooleanField(default=False, verbose_name='سایزبندی دارد؟')
    has_color_option = models.BooleanField(default=False, verbose_name='رنگ بندی دارد؟')

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]
        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = alt_slugify(self.name)
        super().save(*args, **kwargs)

        ProductVariant.objects.filter(product=self).delete()
        if self.has_size_option and self.has_color_option:
            for size in self.size_variants.all():
                for color in self.color_variants.all():
                    ProductVariant.objects.get_or_create(product=self, size=size, color=color)
        elif self.has_size_option and not self.has_color_option:
            for size in self.size_variants.all():
                ProductVariant.objects.get_or_create(product=self, size=size, color=None)
        elif self.has_color_option and not self.has_size_option:
            for color in self.color_variants.all():
                test = ProductVariant.objects.get_or_create(product=self, color=color, size=None)
                print(test)
        else:
            ProductVariant.objects.get_or_create(product=self, size=None, color=None)


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey('ProductSizeVariant', on_delete=models.CASCADE, related_name='variants', null=True, blank=True)
    color = models.ForeignKey('ProductColorVariant', on_delete=models.CASCADE, related_name='variants', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'size', 'color'], name='unique_product_variant')
        ]


class ProductSizeVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='size_variants')
    size = models.CharField(max_length=50, verbose_name='اندازه', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.product.has_size_option and self.size:
            return  # Skip saving if product doesn't support size
        super().save(*args, **kwargs)

    def __str__(self):
        if self.size:
            return f"{self.size if self.size else ''}".strip()
        return f"Default Variant"


class ProductColorVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='color_variants')
    color = models.CharField(max_length=50, verbose_name='رنگ', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.product.has_color_option and self.color:
            return  # Skip saving if product doesn't support color
        super().save(*args, **kwargs)

    def __str__(self):
        if self.color:
            return f"{self.color if self.color else ''}".strip()
        return f"Default Variant"


class ProductFeature(models.Model):
    name = models.CharField(max_length=250, verbose_name='نام ویژگی')
    value = models.CharField(max_length=250, verbose_name='مقدار ویژگی')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='محصول', related_name='features')

    def __str__(self):
        return self.name + ": " + self.value


class Image(models.Model):
    # def delete(self, *args, **kwargs):
    #     storage, path = self.image_file.storage, self.image_file.path
    #     storage.delete(path)
    #     return super().delete(*args, **kwargs)

    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE, verbose_name='محصول')
    create_date = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    image_file = models.ImageField(upload_to='images/%Y/%m/%d', verbose_name='تصویر')
    title = models.CharField(max_length=250, null=True, blank=True, verbose_name='عنوان تصویر')
    description = models.TextField(max_length=250, null=True, blank=True, verbose_name='توضیحات تصویر')


class DiscountCode(models.Model):
    ChoiceType = (
        ('روی مبلغ نهایی (درصد)', 'روی مبلغ نهایی (درصد)'),
        ('روی مبلغ نهایی (مبلغ)', 'روی مبلغ نهایی (مبلغ)'),
        ('روی هزینه ارسال (درصد)', 'روی هزینه ارسال (درصد)'),
    )
    code = models.CharField(max_length=10, verbose_name='کد تخفثیف')
    type = models.CharField(max_length=250, choices=ChoiceType, verbose_name='نوع')
    value = models.PositiveIntegerField(verbose_name='مبلغ یا درصد تخفیف')

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کد های تخفیف'

