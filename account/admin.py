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

    model = ShopUser

    list_display = (
        "phone",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
    )

    fieldsets = (
        (None, {
            "fields": (
                "phone",
                "password",
            )
        }),

        ("اطلاعات شخصی", {
            "fields": (
                "first_name",
                "last_name",
                "email",
            )
        }),

        ("مجوزها", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),

    )


    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "password1",
                    "password2",
                ),
            },
        ),
    )


    search_fields = (
        "phone",
        "first_name",
        "last_name",
    )

    ordering = (
        "phone",
    )


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

    model = ShopSeller

    list_display = (
        "phone",
        "shop_name",
        "first_name",
        "last_name",
        "is_staff",
    )

    ordering = (
        "phone",
    )

    search_fields = (
        "phone",
        "shop_name",
        "first_name",
        "last_name",
    )


    fieldsets = (

        (
            None,
            {
                "fields": (
                    "phone",
                    "password",
                )
            }
        ),

        (
            "اطلاعات مالک",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            }
        ),

        (
            "اطلاعات فروشگاه",
            {
                "fields": (
                    "shop_name",
                    "shop_email",
                    "shop_phone",
                    "shop_address",
                    "logo",
                )
            }
        ),

        (
            "مجوزها",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            }
        ),

    )