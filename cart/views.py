from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.views import View
from django.views.decorators.http import require_POST
from shop.models import Product, ProductVariant
from recommendation.models import Interaction
from cart.cart import Cart
from sms import send_sms


# Create your views here.
def record_cart_interaction(
    request,
    product
):
    """
    ثبت تعامل cart فقط برای کاربران لاگین‌شده.
    """

    if not request.user.is_authenticated:
        return

    Interaction.objects.create(
        user=request.user,
        product=product,
        event="cart",
        source="direct",
    )


@require_POST
def add_to_cart(request, product_id):
    try:
        size_id = request.POST.get('size_id')
        color_id = request.POST.get('color_id')
        product = get_object_or_404(Product, id=product_id)
        if product.has_size_option and product.has_color_option:
            product_variant = get_object_or_404(ProductVariant, product__id=product_id, size__id=size_id,
                                                color__id=color_id)
        elif product.has_size_option and not product.has_color_option:
            product_variant = get_object_or_404(ProductVariant, product__id=product_id, size__id=size_id)
        elif product.has_color_option and not product.has_size_option:
            product_variant = get_object_or_404(ProductVariant, product__id=product_id, color__id=color_id)
        else:
            product_variant = get_object_or_404(ProductVariant, product__id=product_id)
        cart = Cart(request)
        cart.add(product_variant)
        record_cart_interaction(
            request,
            product
        )
        cart_html = render_to_string(
            "includes/cart_dropdown.html",
            {
                "cart": cart,
            },
            request=request,
        )

        response_data = {
            "cart_count": len(cart),
            "cart_html": cart_html,
        }
        return JsonResponse(response_data)
    except:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})


@require_POST
def update_quantity(request):

    item_id = request.POST.get("item_id")
    if item_id:
        item_id = item_id.replace(",", "")
    action = request.POST.get("action")
    print("AJAX ITEM ID:", item_id)

    print(
        "VARIANT EXISTS:",
        ProductVariant.objects.filter(
            id=item_id
        ).exists()
    )
    try:

        product = get_object_or_404(
            ProductVariant,
            id=item_id
        )

        cart = Cart(request)

        # --------------------------------
        # تغییر تعداد
        # --------------------------------

        if action == "add":

            cart.add(product)

            record_cart_interaction(
                request,
                product.product
            )
        elif action == "decrease":

            cart.decrease(product)

        # --------------------------------
        # اطلاعات همین آیتم
        # --------------------------------

        if str(item_id) in cart.cart:

            item_count = cart.cart[str(item_id)]["quantity"]

            total_price = (
                item_count *
                product.product.off_price
            )

            old_total_price = (
                item_count *
                product.product.price
            )

        else:

            item_count = 0
            total_price = 0
            old_total_price = 0

        # --------------------------------
        # رندر مجدد بدنه سبد
        # --------------------------------

        cart_body = render_to_string(
            "includes/cart_dropdown_items.html",
            {
                "cart": cart
            },
            request=request,
        )

        # --------------------------------
        # رندر مجدد فوتر سبد
        # --------------------------------

        cart_footer = render_to_string(
            "includes/cart_dropdown_footer.html",
            {
                "cart": cart
            },
            request=request,
        )

        # --------------------------------
        # پاسخ AJAX
        # --------------------------------

        return JsonResponse({

            "success": True,

            # تعداد کل آیتم‌های سبد
            "cart_count": len(cart),

            # تعداد همین محصول
            "item_count": item_count,

            # شناسه Variant
            "variant_id": product.id,

            # شناسه Product اصلی
            "product_id": product.product.id,

            # قیمت همین آیتم
            "total_price": total_price,

            "old_total_price": old_total_price,

            "off": product.product.off,

            # قیمت‌های کل سبد
            "products_price": cart.total_price(),

            "final_price": cart.final_price(),

            "post_price": cart.post_price(),

            # HTML جدید سبد
            "cart_body": cart_body,

            "cart_footer": cart_footer,

        })

    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "error": str(e)
            },
            status=500
        )


@require_POST
def remove_item(request):
    item_id = request.POST.get('item_id')
    try:
        product = get_object_or_404(ProductVariant, id=item_id)
        cart = Cart(request)
        cart.remove(product)
        cart_html = render_to_string(
            "includes/cart_dropdown.html",
            {
                "cart": cart,
            },
            request=request,
        )
        response_data = {
            'cart_count': len(cart),
            'products_price': cart.total_price(),
            'final_price': cart.final_price(),
            'post_price': cart.post_price(),
            'cart_html': cart_html,
            'item_id': item_id,
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class CartToggleView(View):

    def post(self, request, product_id):

        product = get_object_or_404(
            Product,
            id=product_id
        )

        # -----------------------------------------
        # Variant انتخاب شده توسط کاربر
        # -----------------------------------------

        variant_id = request.POST.get("variant_id")
        print(
            "CART TOGGLE:",
            "product_id =", product_id,
            "variant_id =", variant_id
        )
        if not variant_id:

            return JsonResponse({
                "success": False,
                "error": "هیچ Variant ای انتخاب نشده است."
            })

        product_variant = get_object_or_404(
            ProductVariant,
            id=variant_id,
            product=product
        )
        print(
            "SELECTED VARIANT:",
            product_variant.id,
            "COLOR =",
            product_variant.color.color if product_variant.color else None,
            "SIZE =",
            product_variant.size.size if product_variant.size else None
        )
        # -----------------------------------------
        # Cart
        # -----------------------------------------

        cart = Cart(request)

        variant_key = str(product_variant.id)

        # -----------------------------------------
        # اگر Variant داخل سبد باشد → حذف
        # -----------------------------------------

        if variant_key in cart.cart:

            cart.remove(product_variant)

            status = "removed"
            item_count = 0

        # -----------------------------------------
        # اگر داخل سبد نباشد → اضافه
        # -----------------------------------------

        else:

            cart.add(product_variant)

            record_cart_interaction(
                request,
                product
            )

            status = "added"

            item_count = cart.cart[
                variant_key
            ]["quantity"]

        # -----------------------------------------
        # بدنه Dropdown
        # -----------------------------------------

        cart_body = render_to_string(
            "includes/cart_dropdown_items.html",
            {
                "cart": cart
            },
            request=request,
        )

        # -----------------------------------------
        # Footer
        # -----------------------------------------

        cart_footer = render_to_string(
            "includes/cart_dropdown_footer.html",
            {
                "cart": cart
            },
            request=request,
        )

        # -----------------------------------------
        # Response
        # -----------------------------------------

        return JsonResponse({

            "success": True,

            "status": status,

            "product_id": product.id,

            "variant_id": product_variant.id,

            "item_count": item_count,

            "cart_count": len(cart),

            "products_price": cart.total_price(),

            "post_price": cart.post_price(),

            "final_price": cart.final_price(),

            "cart_body": cart_body,

            "cart_footer": cart_footer,

            "is_empty": len(cart) == 0,
        })