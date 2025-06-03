from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product, ProductVariant
from cart.cart import Cart
from sms import send_sms


# Create your views here.

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
        response_data = {
            'cart_count': len(cart)
        }
        return JsonResponse(response_data)
    except:
        return JsonResponse({'error': 'Invalid request'}, status=400)


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})


@require_POST
def update_quantity(request):
    item_id = request.POST.get('item_id')
    action = request.POST.get('action')

    try:
        product = get_object_or_404(ProductVariant, id=item_id)
        print(product)
        cart = Cart(request)

        if action == 'add':
            cart.add(product)
        elif action == 'decrease':
            cart.decrease(product)
        else:
            return JsonResponse({'error': 'Invalid action'}, status=400)

        cart_item = cart.cart[item_id]
        print(cart_item)

        response_data = {
            'cart_count': len(cart),
            'item_count': cart.cart[str(item_id)]['quantity'],
            'total_price': cart_item['quantity'] * product.product.off_price,
            'products_price': cart.total_price(),
            'final_price': cart.final_price(),
            'post_price': cart.post_price()
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def remove_item(request):
    item_id = request.POST.get('item_id')
    try:
        product = get_object_or_404(ProductVariant, id=item_id)
        cart = Cart(request)
        cart.remove(product)
        response_data = {
            'cart_count': len(cart),
            'products_price': cart.total_price(),
            'final_price': cart.final_price(),
            'post_price': cart.post_price()
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

