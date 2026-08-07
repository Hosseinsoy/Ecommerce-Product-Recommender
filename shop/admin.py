from django.contrib import admin

from .models import (
    Product,
    Image,
    ProductFeature,
    DiscountCode,
    ProductSizeVariant,
    ProductColorVariant,
    ProductVariant,
    Brand,
    ProductComment,
    CommentPoint,
    ProductCommentPoint,
)

from shop.models import Category


# =========================================================
# Product Inlines
# =========================================================

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


# =========================================================
# Product
# =========================================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'category',
        'inventory',
        'price',
        'off',
        'created',
        'updated',
    )

    list_filter = (
        'inventory',
        'category',
        'created',
        'updated',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }

    search_fields = (
        'name',
        'description',
    )

    readonly_fields = (
        'off_price',
    )

    inlines = [
        ProductFeatureInline,
        ImageInline,
        ProductSizeVariantInline,
        ProductColorVariantInline,
    ]


# =========================================================
# Product Variant
# =========================================================

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'size',
        'color',
    )


# =========================================================
# Category
# =========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        'name',
    )

    prepopulated_fields = {
        'slug': ('name',)
    }


# =========================================================
# Discount Code
# =========================================================

@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):

    list_display = (
        'code',
        'type',
        'value',
    )


# =========================================================
# Brand
# =========================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'slug',
        'logo',
        'description',
        'is_active',
        'created',
    )


# =========================================================
# Comment Point
# =========================================================

@admin.register(CommentPoint)
class CommentPointAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
    )

    search_fields = (
        'title',
    )

    ordering = (
        'id',
    )


# =========================================================
# Product Comment Point Inline
# =========================================================

class ProductCommentPointInline(admin.TabularInline):

    model = ProductCommentPoint

    extra = 1

    fields = (
        'point',
        'point_type',
    )


# =========================================================
# Product Comment
# =========================================================

@admin.register(ProductComment)
class ProductCommentAdmin(admin.ModelAdmin):

    list_display = (
        'product',
        'user',
        'title',
        'score',
        'is_recommended',
        'is_buyer',
        'likes',
        'dislikes',
        'is_active',
        'created',
        'updated',
    )

    list_filter = (
        'score',
        'is_recommended',
        'is_buyer',
        'is_active',
        'created',
    )

    search_fields = (
        'title',
        'body',
        'product__name',
        'user__phone',
        'user__first_name',
        'user__last_name',
    )

    readonly_fields = (
        'created',
        'updated',
    )

    ordering = (
        '-created',
    )

    inlines = [
        ProductCommentPointInline,
    ]


# =========================================================
# Product Comment Point
# =========================================================

# @admin.register(ProductCommentPoint)
# class ProductCommentPointAdmin(admin.ModelAdmin):
#
#     list_display = (
#         'id',
#         'comment',
#         'point',
#         'point_type',
#     )
#
#     list_filter = (
#         'point_type',
#     )
#
#     search_fields = (
#         'comment__title',
#         'point__title',
#         'comment__product__name',
#     )
#
#     ordering = (
#         'id',
#     )