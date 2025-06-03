from itertools import product

from django.contrib import messages
from django.contrib.auth.decorators import login_required
# from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.http import JsonResponse

from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string

from account.models import ShopUser
from cart.cart import Cart
from .forms import SearchForm
from .models import Category, Product, DiscountCode
from django.conf import settings
from django_filters.views import FilterView
from .filters import ProductFilter

User = settings.AUTH_USER_MODEL


# Create your views here.
# def product_list(request, category_slug=None, base_on=None):
#     category = None
#     categories = Category.objects.all()
#     products = Product.objects.all()
#     if category_slug:
#         category = get_object_or_404(Category, slug=category_slug)
#         products = products.filter(category=category)
#     if base_on:
#         if base_on == 'newest':
#             products = products.order_by('-created')
#         elif base_on == 'cheapest':
#             products = products.order_by('price')
#         elif base_on == 'most_expensive':
#             products = products.order_by('-price')
#     context = {
#         'category': category,
#         'categories': categories,
#         'products': products
#     }
#     return render(request, 'shop/product_list.html', context)


class ProductListView(FilterView):
    model = Product
    queryset = Product.objects.all().order_by('-is_available', '-created')
    filterset_class = ProductFilter
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    if count := (Product.objects.all().count() // paginate_by).is_integer():
        pages_count = count
    else:
        pages_count = int(count) + 1
    extra_context = {
        'pages_count': pages_count,
    }


def product_detail(request, id, slug):
    if 'discounted_cost' in request.session:
        del request.session['discounted_cost']
    product = get_object_or_404(Product, id=id, slug=slug)
    categories = Category.objects.all()
    related_products = Product.objects.filter(name__startswith=product.name.split(' ')[0]).exclude(id=id)
    product_orders = product.orders.all()
    recommended_products = []
    for order in product_orders:
        for p in order.order.items.all():
            if id != p.product.id:
                recommended_products.append(p.product)
    context = {
        'product': product,
        'categories': categories,
        'related_products': related_products,
        'recommended_products': recommended_products,
    }
    return render(request, 'shop/product_detail.html', context)


def search(request):
    query = None
    result = []
    form = SearchForm(request.POST)

    if 'query' in request.POST:
        if form.is_valid():
            query = form.cleaned_data['query']
            # result1 = Product.objects.annotate(similarity=TrigramSimilarity('name', query)).filter(similarity__gte=0.1)
            # result2 = Product.objects.annotate(similarity=TrigramSimilarity('description', query)).filter(
            #     similarity__gte=0.1)
            # result = (result1 | result2).order_by('-similarity')
            result = Product.objects.filter(name__icontains=query).distinct()

    context = {
        'query': query,
        'result': result,
    }

    return render(request, 'shop/search_result.html', context)


@login_required
def save_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = ShopUser.objects.get(id=request.user.id)
    if product in user.saved_products.all():
        saved = False
        user.saved_products.remove(product)
    else:
        saved = True
        user.saved_products.add(product)
    return JsonResponse(data={'saved': saved})


def add_discount_code(request):
    if request.method == 'POST':
        discount_code = request.POST.get('discount_code')
        try:
            dc = DiscountCode.objects.get(code=discount_code)
            cart = Cart(request)
            messages.success(request, 'کد تخفیف اعمال شد')
            request.session['discounted_cost'] = cart.price_after_discount_code(dc)
            request.session['discount_code'] = dc.id
        except DiscountCode.DoesNotExist:
            messages.error(request, 'کد تخفیف اشتباه است')
        return redirect('order:create_order')

    else:
        template = render_to_string('partials/discount_code.html', request=request)
        return JsonResponse({'template': template})


