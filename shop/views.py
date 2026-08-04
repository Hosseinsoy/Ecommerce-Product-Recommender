from itertools import product, zip_longest

from django.contrib import messages
from django.contrib.auth.decorators import login_required
# from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.http import JsonResponse

from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import ListView

from account.models import ShopUser
from cart.cart import Cart
from .forms import SearchForm
from .models import Category, Product, DiscountCode, Brand
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


def home(request):

    flash_products = [
        product for product in Product.objects.prefetch_related(
            'images',
            'variants'
        )
        if product.is_flash_sale
    ][:10]

    popular_brands = Brand.objects.filter(
    ).order_by('-sales_count')[:12]

    newest_products = Product.objects.prefetch_related(
        'images'
    ).filter(
        is_available=True
    ).order_by('-created')[:12]

    def chunked(iterable, n):
        args = [iter(iterable)] * n
        return zip_longest(*args)

    context = {
        'shocking_products': flash_products,
        'popular_brands': popular_brands,
        "newest_products": chunked(newest_products, 3),
    }

    return render(request, 'shop/home.html', context)


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


class CategoryDetailView(ListView):
    model = Product
    template_name = "shop/category_detail.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs["slug"]
        )

        return (
            Product.objects
            .filter(
                category=self.category,
                is_available=True
            )
            .prefetch_related(
                "images",
                "variants"
            )
            .select_related(
                "brand",
                "category"
            )
            .order_by("-created")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["category"] = self.category

        context["categories"] = Category.objects.all().order_by("name")

        context["brands"] = Brand.objects.filter(
            products__category=self.category,
            products__is_available=True,
        ).distinct().order_by("name")

        products = self.get_queryset()

        context["min_price"] = (
            products.order_by("price").first().price
            if products.exists() else 0
        )

        context["max_price"] = (
            products.order_by("-price").first().price
            if products.exists() else 0
        )

        return context


class CategoryBrandsAjaxView(View):
    def get(self, request):
        category_ids = request.GET.getlist("categories")
        brands = (
            Brand.objects
            .filter(
                products__category__id__in=category_ids,
                products__is_available=True
            )
            .distinct()
            .order_by("name")
        )

        data = []

        for brand in brands:
            data.append({
                "id": brand.id,
                "name": brand.name,
            })

        return JsonResponse(data, safe=False)


class CategoryProductsAjaxView(View):

    def get(self, request, slug):

        category = get_object_or_404(Category, slug=slug)

        # -------------------------------
        # دسته بندی
        # -------------------------------
        category_ids = request.GET.getlist("categories")

        if category_ids:
            products = Product.objects.filter(
                category_id__in=category_ids
            )
        else:
            products = Product.objects.filter(
                category__slug=slug
            )
        products = (
            products
            .select_related(
                "brand",
                "category"
            )
            .prefetch_related(
                "images",
                "variants"
            )
        )

        # -------------------------------
        # برند
        # -------------------------------
        brand_ids = request.GET.getlist("brands")

        if brand_ids:
            products = products.filter(
                brand_id__in=brand_ids
            )

        # -------------------------------
        # قیمت
        # -------------------------------
        min_price = request.GET.get("min_price")
        max_price = request.GET.get("max_price")

        if min_price:
            products = products.filter(
                off_price__gte=min_price
            )

        if max_price:
            products = products.filter(
                off_price__lte=max_price
            )

        # -------------------------------
        # فقط کالاهای موجود
        # -------------------------------
        only_available = request.GET.get("only_available")

        if only_available == "1":
            products = products.filter(
                inventory__gt=0
            )

        # -------------------------------
        # مرتب سازی
        # -------------------------------
        sort = request.GET.get("sort", "newest")

        if sort == "newest":
            products = products.order_by("-created")

        elif sort == "oldest":
            products = products.order_by("created")

        elif sort == "cheap":
            products = products.order_by("off_price", "price")

        elif sort == "expensive":
            products = products.order_by("-off_price", "-price")

        # -------------------------------
        # صفحه بندی
        # -------------------------------
        paginator = Paginator(products, 12)

        page = request.GET.get("page")

        page_obj = paginator.get_page(page)

        html = render_to_string(
            "includes/products_list.html",
            {
                "page_obj": page_obj,
                "products": page_obj.object_list,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
            },
            request=request
        )

        return JsonResponse({
            "html": html,
            "count": paginator.count,
        })


def brand_detail(request, brand_name):
    pass