from order.models import Order
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# Create your models here.

class ShopUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Users must have phone number')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        self.create_user(phone, password, **extra_fields)


class ShopSeller(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=11, unique=True, verbose_name='شماره تلفن مالک')
    email = models.EmailField(unique=True, blank=True, null=True, verbose_name='ایمیل مالک')
    first_name = models.CharField(max_length=50, verbose_name='نام مالک')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی مالک')
    shop_name = models.CharField(max_length=100, verbose_name='نام فروشگاه')
    shop_email = models.EmailField(max_length=100, null=True, blank=True, verbose_name='ایمیل فروشگاه')
    shop_phone = models.CharField(max_length=100, unique=True, verbose_name='شماره تلفن فروشگاه')
    shop_address = models.CharField(max_length=100, verbose_name='آدرس فروشگاه')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    objects = ShopUserManager()
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='shop_seller_set',  # Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='shop_seller_permissions',  # Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def get_full_name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return self.shop_name


class ShopUser(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=11, unique=True, verbose_name='شماره تلفن')
    email = models.EmailField(unique=True, blank=True, null=True)
    first_name = models.CharField(max_length=50, verbose_name='نام')
    last_name = models.CharField(max_length=50, verbose_name='نام خانوادگی')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    saved_products = models.ManyToManyField('shop.Product', related_name='saved_by', verbose_name='محصولات ذخیره شده: ')
    objects = ShopUserManager()
    USERNAME_FIELD = 'phone'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='shop_user_set',  # Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='shop_user_permissions',  # Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.phone

    def get_full_name(self):
        return '%s %s' % (self.first_name, self.last_name)


class UserAddress(models.Model):
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE, related_name='addresses')
    province = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    address = models.TextField(max_length=100)
    house_number = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10, default='')

    def __str__(self):
        return f"{self.province} | {self.city} | {self.address} پلاک: {self.house_number} | " + 'کد پستی' + f":{self.postal_code}"


class Province(models.Model):
    name = models.CharField(max_length=50, verbose_name='نام استان')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'استان'
        verbose_name_plural = 'استان ها'


class City(models.Model):
    name = models.CharField(max_length=50, verbose_name='نام شهر')
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='cities')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'شهر'
        verbose_name_plural = 'شهر ها'
