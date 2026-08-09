from django.db.models import Avg
from django.utils import timezone
from django.db import models
from django.utils.text import slugify
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

    def get_absolute_url(self):
        return reverse(
            "shop:category_detail",
            kwargs={"slug": self.slug}
        )

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='نام برند'
    )

    slug = models.SlugField(
        max_length=120,
        unique=True,
        blank=True
    )

    logo = models.ImageField(
        upload_to='brands/',
        blank=True,
        null=True,
        verbose_name='لوگو'
    )

    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    sales_count = models.PositiveIntegerField(verbose_name='تعداد فروش', default=0)

    created = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'برند'
        verbose_name_plural = 'برندها'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('shop:brand_products', args=[self.slug])


class Product(models.Model):
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='برند',
        null=True,
        blank=True
    )
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
    flash_sale_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='شروع شگفت انگیز'
    )

    flash_sale_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='پایان شگفت انگیز'
    )

    from django.utils import timezone

    @property
    def is_flash_sale(self):
        now = timezone.localtime()

        return (
                self.off >= 10 and
                self.flash_sale_start and
                self.flash_sale_end and
                self.flash_sale_start <= now <= self.flash_sale_end
        )


    @property
    def average_score(self):
        return self.comments.filter(
            is_active=True,
            is_buyer=True
        ).aggregate(
            avg=Avg("score")
        )["avg"] or 0

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


class ProductSeller(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sellers'
    )

    seller = models.ForeignKey(
        'account.ShopSeller',
        on_delete=models.CASCADE,
        related_name='selling_products'
    )

    price = models.PositiveIntegerField(
        verbose_name='قیمت فروشنده'
    )

    inventory = models.PositiveIntegerField(
        default=0,
        verbose_name='موجودی فروشنده'
    )

    warranty = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='گارانتی'
    )

    satisfaction = models.PositiveIntegerField(
        default=0,
        verbose_name='رضایت مشتری'
    )

    performance = models.CharField(
        max_length=50,
        default='عالی',
        verbose_name='عملکرد'
    )

    shipping_type = models.CharField(
        max_length=100,
        default='ارسال شاپیک',
        verbose_name='نوع ارسال'
    )


    class Meta:
        unique_together = ('product', 'seller')


    def __str__(self):
        return f'{self.product.name} - {self.seller.shop_name}'


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


from django.db import models
from django.conf import settings


class ProductComment(models.Model):

    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='محصول'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_comments',
        verbose_name='کاربر'
    )

    title = models.CharField(
        max_length=200,
        verbose_name='عنوان دیدگاه'
    )

    body = models.TextField(
        max_length=2000,
        verbose_name='متن دیدگاه'
    )

    # ---------------------------------
    # امتیاز ستاره‌ای
    # ---------------------------------

    score = models.PositiveIntegerField(
        default=5,
        verbose_name='امتیاز'
    )

    # ---------------------------------
    # پیشنهاد خرید
    # ---------------------------------

    is_recommended = models.BooleanField(
        default=True,
        verbose_name='پیشنهاد می‌کنم'
    )

    # ---------------------------------
    # لایک و دیسلایک
    # ---------------------------------

    likes = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد پسند'
    )

    dislikes = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد نپسند'
    )

    # ---------------------------------
    # آیا خریدار محصول بوده؟
    # ---------------------------------

    is_buyer = models.BooleanField(
        default=False,
        verbose_name='خریدار محصول'
    )

    # ---------------------------------
    # زمان‌ها
    # ---------------------------------

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت'
    )

    updated = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین تغییر'
    )

    # ---------------------------------
    # فعال / غیرفعال
    # ---------------------------------

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    # ---------------------------------
    # موضوعات مثبت و منفی
    # ---------------------------------

    points = models.ManyToManyField(
        'CommentPoint',
        through='ProductCommentPoint',
        related_name='comments',
        blank=True,
        verbose_name='موضوعات دیدگاه'
    )

    positive_points = models.TextField(
        blank=True,
        null=True,
        verbose_name="نکات مثبت"
    )

    negative_points = models.TextField(
        blank=True,
        null=True,
        verbose_name="نکات منفی"
    )

    class Meta:

        ordering = ['-created']

        verbose_name = 'دیدگاه'
        verbose_name_plural = 'دیدگاه‌ها'

        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_user_product_comment'
            )
        ]

    @property
    def rating(self):
        """
        برای استفاده راحت‌تر در Template
        """
        return self.score

    def __str__(self):
        return f'{self.product.name} - {self.user}'


class CommentPoint(models.Model):

    title = models.CharField(
        max_length=100,
        verbose_name='موضوع'
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'موضوع کامنت'
        verbose_name_plural = 'موضوعات کامنت'


class ProductCommentPoint(models.Model):

    POINT_TYPE_CHOICES = (
        ('positive', 'مثبت'),
        ('negative', 'منفی'),
    )

    comment = models.ForeignKey(
        ProductComment,
        on_delete=models.PROTECT,
        related_name='comment_points',
        verbose_name='دیدگاه'
    )

    point = models.ForeignKey(
        CommentPoint,
        on_delete=models.PROTECT,
        related_name='comment_relations',
        verbose_name='موضوع'
    )

    point_type = models.CharField(
        max_length=10,
        choices=POINT_TYPE_CHOICES,
        verbose_name='نوع'
    )

    class Meta:
        verbose_name = 'موضوع دیدگاه محصول'
        verbose_name_plural = 'موضوعات دیدگاه محصول'

        constraints = [
            models.UniqueConstraint(
                fields=['comment', 'point'],
                name='unique_comment_point'
            )
        ]

    def __str__(self):
        return (
            f'{self.comment} - '
            f'{self.point} - '
            f'{self.get_point_type_display()}'
        )


class ProductQuestion(models.Model):

    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='محصول'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_questions',
        verbose_name='کاربر'
    )

    body = models.TextField(
        max_length=1000,
        verbose_name='متن پرسش'
    )

    # لایک و دیسلایک پرسش
    likes = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد پسند'
    )

    dislikes = models.PositiveIntegerField(
        default=0,
        verbose_name='تعداد نپسند'
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    class Meta:
        ordering = ['-created']
        verbose_name = 'پرسش محصول'
        verbose_name_plural = 'پرسش‌های محصول'

    def __str__(self):
        return f'{self.product.name} - {self.user}'


class ProductAnswer(models.Model):

    question = models.ForeignKey(
        ProductQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='پرسش'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_answers',
        verbose_name='کاربر'
    )

    body = models.TextField(
        max_length=1500,
        verbose_name='متن پاسخ'
    )

    is_seller = models.BooleanField(
        default=False,
        verbose_name='پاسخ فروشنده'
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ ثبت'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='فعال'
    )

    class Meta:
        ordering = ['created']
        verbose_name = 'پاسخ پرسش'
        verbose_name_plural = 'پاسخ‌های پرسش'

    def __str__(self):
        return f'پاسخ به پرسش {self.question_id} - {self.user}'