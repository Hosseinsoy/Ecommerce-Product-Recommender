from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import ShpUserChangedForm, ShpUserCreationForm, ShpSellerCreationForm, ShopSellerChangedForm

from .models import ShopUser, UserAddress, Province, City, ShopSeller


# Register your models here.

class UserAddressInline(admin.StackedInline):
    model = UserAddress
    extra = 0

@admin.register(ShopUser)
class ShopUserAdmin(UserAdmin):
    ordering = ('phone',)
    list_display = ('phone', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    add_form = ShpUserCreationForm
    form = ShpUserChangedForm
    inlines = [UserAddressInline]

    fieldsets = [
        (None, {'fields': ['phone', 'password']}),
        ('Personal Information', {'fields': ['first_name', 'last_name', 'email', 'saved_products']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Important Dates', {'fields': ['last_login', 'date_joined']}),
    ]

    add_fieldsets = [
        (None, {'fields': ['phone', 'password1', 'password2']}),
        ('Personal Information', {'fields': ['first_name', 'last_name', 'email']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Important Dates', {'fields': ['last_login', 'date_joined']}),
    ]


class CitiesInline(admin.StackedInline):
    model = City
    extra = 0


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    ordering = ('name',)
    list_display = ('name',)
    inlines = [CitiesInline]


@admin.register(ShopSeller)
class ShopSellerAdmin(UserAdmin):
    ordering = ('shop_name',)
    list_display = ('shop_name', 'shop_phone', 'shop_address', 'date_joined')
    add_form = ShpSellerCreationForm
    form = ShopSellerChangedForm

    fieldsets = [
        (None, {'fields': ['phone', 'password']}),
        ('Personal Information', {'fields': ['first_name', 'last_name', 'email', 'shop_name', 'shop_phone', 'shop_address']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Important Dates', {'fields': ['last_login', 'date_joined']}),
    ]

    add_fieldsets = [
        (None, {'fields': ['phone', 'password1', 'password2']}),
        ('Personal Information', {'fields': ['first_name', 'last_name', 'email', 'shop_name', 'shop_phone', 'shop_address']}),
        ('Permissions', {'fields': ['is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions']}),
        ('Important Dates', {'fields': ['last_login', 'date_joined']}),
    ]
