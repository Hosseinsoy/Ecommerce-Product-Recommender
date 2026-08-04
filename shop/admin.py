from django.contrib import admin
from .models import Product, Image, ProductFeature, DiscountCode, ProductSizeVariant, ProductColorVariant, \
    ProductVariant, Brand

from shop.models import Category


# Inlines
class ImageInline(admin.TabularInline):
    model = Image
    extra = 0


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 0


class ProductSizeVariantInline(admin.TabularInline):
    model = ProductSizeVariant
    extra = 0


class ProductColorVariantInline(admin.TabularInline):
    model = ProductColorVariant
    extra = 0


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'inventory', 'price', 'off', 'created', 'updated')
    list_filter = ('inventory', 'category', 'created', 'updated')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    readonly_fields = ['off_price']
    inlines = [ProductFeatureInline, ImageInline, ProductSizeVariantInline, ProductColorVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'size', 'color']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'type', 'value']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'logo', 'description', 'is_active', 'created']