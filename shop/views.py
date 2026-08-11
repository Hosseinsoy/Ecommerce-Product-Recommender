from itertools import product, zip_longest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# from django.contrib.postgres.search import TrigramSimilarity
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from account.models import ShopUser
from cart.cart import Cart
from order.models import OrderItem
from .forms import SearchForm
from django.db.models import Min, Max, Q, Avg, Count, F, Sum, Value
from .models import Category, Product, DiscountCode, Brand, ProductComment, CommentPoint, ProductCommentPoint, \
    ProductQuestion, ProductAnswer
from django.conf import settings
from django_filters.views import FilterView
from .filters import ProductFilter
from django.contrib.auth.mixins import LoginRequiredMixin
from shop.utils.wishlist import (
    get_wishlist,
    save_wishlist,
)

User = settings.AUTH_USER_MODEL

PRODUCTS_PER_PAGE = 12  # 4X

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


class ProductListView(ListView):
    model = Product
    template_name = "shop/product_list.html"
    context_object_name = "products"
    paginate_by = PRODUCTS_PER_PAGE


    def get_queryset(self):

        products = (
            Product.objects
            .filter(
                is_available=True
            )
            .select_related(
                "brand",
                "category"
            )
            .prefetch_related(
                "images",
                "variants"
            )
        )


        # ---------------------
        # Category Filter
        # ---------------------

        category_ids = self.request.GET.getlist(
            "categories"
        )

        if category_ids:

            products = products.filter(
                category_id__in=category_ids
            )


        # ---------------------
        # Brand Filter
        # ---------------------

        brand_ids = self.request.GET.getlist(
            "brands"
        )

        if brand_ids:

            products = products.filter(
                brand_id__in=brand_ids
            )


        # ---------------------
        # Price
        # ---------------------

        min_price = self.request.GET.get(
            "min_price"
        )

        max_price = self.request.GET.get(
            "max_price"
        )


        if min_price:
            products = products.filter(
                off_price__gte=min_price
            )


        if max_price:
            products = products.filter(
                off_price__lte=max_price
            )


        # ---------------------
        # موجودی
        # ---------------------

        only_available = self.request.GET.get(
            "only_available"
        )


        if only_available != "0":

            products = products.filter(
                inventory__gt=0
            )


        # ---------------------
        # Ordering
        # ---------------------

        sort = self.request.GET.get(
            "sort",
            "newest"
        )


        if sort == "newest":

            products = products.order_by(
                "-created"
            )


        elif sort == "oldest":

            products = products.order_by(
                "created"
            )


        elif sort == "cheap":

            products = products.order_by(
                "off_price",
                "price"
            )


        elif sort == "expensive":

            products = products.order_by(
                "-off_price",
                "-price"
            )


        return products

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["categories"] = Category.objects.all()

        selected_categories = [
            int(x)
            for x in self.request.GET.getlist("categories")
        ]

        context["selected_categories"] = selected_categories

        # -----------------------------
        # برندها بر اساس دسته بندی
        # -----------------------------

        if selected_categories:

            context["brands"] = Brand.objects.filter(
                products__category_id__in=selected_categories
            ).distinct()

        else:

            context["brands"] = Brand.objects.none()

        context["selected_brands"] = [
            int(x)
            for x in self.request.GET.getlist("brands")
        ]

        context["only_available"] = (
                self.request.GET.get("only_available", "1")
                == "1"
        )

        context["current_sort"] = self.request.GET.get(
            "sort",
            "newest"
        )

        return context


def product_detail(request, id, slug):

    if 'discounted_cost' in request.session:
        del request.session['discounted_cost']

    product = get_object_or_404(
        Product,
        id=id,
        slug=slug
    )

    # -----------------------------------------
    # بررسی وجود محصول در سبد خرید
    # -----------------------------------------

    cart = Cart(request)

    cart_product_ids = {
        item["product"].product.id
        for item in cart
    }

    product_in_cart = product.id in cart_product_ids

    categories = Category.objects.all()

    related_products = (
        Product.objects
        .filter(
            name__startswith=product.name.split(' ')[0]
        )
        .exclude(id=id)
    )

    product_orders = product.orders.all()

    recommended_products = []

    for order in product_orders:
        for p in order.order.items.all():
            if id != p.product.id:
                recommended_products.append(p.product)

    # -----------------------------------------
    # مرتب‌سازی کامنت‌ها
    # -----------------------------------------

    comment_sort = request.GET.get(
        "comment_sort",
        "newest"
    )

    comments = (
        product.comments
        .select_related("user")
    )

    if comment_sort == "buyers":

        comments = comments.filter(
            is_buyer=True
        ).order_by(
            "-created"
        )

    elif comment_sort == "useful":

        comments = comments.annotate(
            usefulness=F("likes") - F("dislikes")
        ).order_by(
            "-usefulness",
            "-created"
        )

    else:

        comments = comments.order_by(
            "-created"
        )

    # -----------------------------------------
    # اگر درخواست AJAX بود
    # -----------------------------------------

    if request.GET.get("ajax") == "1":

        html = render_to_string(
            "includes/product_comments.html",
            {
                "comments": comments,
                "product": product,
            },
            request=request
        )

        return JsonResponse({
            "html": html
        })

    # -----------------------------------------
    # ادامه اطلاعات صفحه
    # -----------------------------------------

    total_comments = comments.count()

    comment_points = (
        CommentPoint.objects
        .annotate(
            positive_count=Count(
                "comment_relations",
                filter=Q(
                    comment_relations__comment__product=product,
                    comment_relations__point_type="positive",
                    comment_relations__comment__is_active=True,
                ),
                distinct=True,
            ),
            negative_count=Count(
                "comment_relations",
                filter=Q(
                    comment_relations__comment__product=product,
                    comment_relations__point_type="negative",
                    comment_relations__comment__is_active=True,
                ),
                distinct=True,
            ),
        )
    )

    comment_points = [
        point
        for point in comment_points
        if point.positive_count > 0
        or point.negative_count > 0
    ]

    for point in comment_points:

        point.total_count = (
            point.positive_count +
            point.negative_count
        )

        if total_comments > 0:

            point.positive_percent = (
                point.positive_count /
                total_comments
            ) * 100

            point.negative_percent = (
                point.negative_count /
                total_comments
            ) * 100

            point.gray_percent = max(
                0,
                100
                - point.positive_percent
                - point.negative_percent
            )

        else:

            point.positive_percent = 0
            point.negative_percent = 0
            point.gray_percent = 100

    buyer_comments = comments.filter(
        is_buyer=True
    )

    agg = buyer_comments.aggregate(
        avg=Avg("score"),
        count=Count("id")
    )

    if agg["avg"] is None:

        average_rating = 0
        rating_count = 0

    else:

        rating_count = agg["count"]
        average_rating = agg["avg"]

    full_stars = int(average_rating)

    decimal_part = (
        average_rating -
        full_stars
    )

    star_percentage = round(
        decimal_part * 100
    )

    comment_points_list = (
        CommentPoint.objects.all()
    )

    questions = (
        product.questions
        .filter(is_active=True)
        .prefetch_related(
            "answers__user"
        )
        .select_related("user")
        .order_by("-created")
    )
    if request.user.is_authenticated:
        product_in_wishlist = request.user.saved_products.filter(
            id=product.id
        ).exists()
    else:
        wishlist = get_wishlist(request.session)
        product_in_wishlist = product.id in wishlist

    context = {

        "product": product,
        "categories": categories,
        "related_products": related_products,
        "recommended_products": recommended_products,

        "comments": comments,

        "average_rating": average_rating,
        "rating_count": rating_count,

        "full_stars": full_stars,
        "decimal_part": decimal_part,
        "star_percentage": star_percentage,

        "comment_points": comment_points,
        "total_comments": total_comments,

        "comment_points_list": comment_points_list,

        "comment_sort": comment_sort,
        "questions": questions,
        "product_in_cart": product_in_cart,
        "product_in_wishlist": product_in_wishlist,
    }

    return render(
        request,
        "shop/product_detail.html",
        context
    )


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
    if request.method != 'POST':
        return redirect('order:create_order')

    discount_code = request.POST.get('discount_code', '').strip()

    if not discount_code:
        messages.error(request, 'کد تخفیف را وارد کنید')
        return redirect('order:create_order')

    try:
        dc = DiscountCode.objects.get(code=discount_code)

    except DiscountCode.DoesNotExist:
        messages.error(request, 'کد تخفیف اشتباه است')
        return redirect('order:create_order')

    cart = Cart(request)

    discounted_cost = cart.price_after_discount_code(dc)

    request.session['discounted_cost'] = discounted_cost
    request.session['discount_code'] = dc.id
    request.session['discount_code_value'] = dc.code

    messages.success(
        request,
        f'کد تخفیف اعمال شد.'
    )

    return redirect('order:create_order')


class CategoryDetailView(ListView):
    model = Product
    template_name = "shop/category_detail.html"
    context_object_name = "products"
    paginate_by = PRODUCTS_PER_PAGE

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs["slug"]
        )

        products = (
            Product.objects
            .filter(is_available=True)
            .prefetch_related(
                "images",
                "variants"
            )
            .select_related(
                "brand",
                "category"
            )
        )

        # -------------------------
        # Category Filter
        # -------------------------
        category_ids = self.request.GET.getlist("categories")

        if category_ids:
            products = products.filter(category__id__in=category_ids)
        else:
            products = products.filter(category=self.category)

        # -------------------------
        # Brand Filter
        # -------------------------
        brand_ids = self.request.GET.getlist("brands")

        if brand_ids:
            products = products.filter(brand__id__in=brand_ids)

        # -------------------------
        # Price Filter
        # -------------------------
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        # -------------------------
        # Ordering
        # -------------------------
        sort = self.request.GET.get("sort", "newest")

        if sort == "newest":
            products = products.order_by("-created")

        elif sort == "oldest":
            products = products.order_by("created")

        elif sort == "cheap":
            products = products.order_by("off_price", "price")

        elif sort == "expensive":
            products = products.order_by("-off_price", "-price")

        return products

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["category"] = self.category

        context["categories"] = Category.objects.all().order_by("name")

        context["brands"] = (
            Brand.objects.filter(
                products__category=self.category
            )
            .distinct()
            .order_by("name")
        )
        if self.request.user.is_authenticated:

            context["saved_product_ids"] = list(
                self.request.user.saved_products.values_list(
                    "id",
                    flat=True
                )
            )

        else:

            context["saved_product_ids"] = self.request.session.get(
                "wishlist",
                []
            )
        from cart.cart import Cart

        cart = Cart(self.request)

        context["cart_item_ids"] = [
            int(item["product"].id)
            for item in cart
        ]

        products = self.get_queryset()

        default_min = (
            products.order_by("price").first().price
            if products.exists() else 0
        )

        default_max = (
            products.order_by("-price").first().price
            if products.exists() else 0
        )

        context["min_price"] = self.request.GET.get("min_price", default_min)
        context["max_price"] = self.request.GET.get("max_price", default_max)

        context["selected_brands"] = [
            int(x)
            for x in self.request.GET.getlist("brands")
        ]

        context["only_available"] = (
                self.request.GET.get("only_available") == "1"
                or "only_available" not in self.request.GET
        )

        context["current_sort"] = self.request.GET.get(
            "sort",
            "newest"
        )
        if self.request.GET.getlist("categories"):

            context["selected_categories"] = [
                int(x)
                for x in self.request.GET.getlist("categories")
            ]

        else:

            context["selected_categories"] = [
                self.category.id
            ]
        context["selected_brands"] = [
            int(x) for x in self.request.GET.getlist("brands")
        ]
        context["current_sort"] = self.request.GET.get("sort", "newest")
        context["is_wishlist_page"] = False
        return context


class CategoryBrandsAjaxView(View):
    def get(self, request):

        category_ids = request.GET.getlist("categories")

        brands = (
            Brand.objects
            .filter(
                products__category__id__in=category_ids
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


    def get(self, request, type, slug):

        # -------------------------------
        # منبع صفحه (Category / Brand)
        # -------------------------------

        if type == "category":

            category = get_object_or_404(
                Category,
                slug=slug
            )

            products = Product.objects.all()


        elif type == "brand":

            brand = get_object_or_404(
                Brand,
                slug=slug
            )

            products = Product.objects.filter(
                brand=brand
            )

        else:

            return JsonResponse(
                {
                    "error": "invalid source"
                },
                status=400
            )



        # -------------------------------
        # دسته بندی فیلتر
        # -------------------------------

        category_ids = request.GET.getlist("categories")

        if category_ids:

            products = products.filter(
                category_id__in=category_ids
            )

        elif type == "category":

            products = products.filter(
                category=category
            )



        # -------------------------------
        # برند فیلتر
        # -------------------------------

        brand_ids = request.GET.getlist("brands")


        if brand_ids:

            products = products.filter(
                brand_id__in=brand_ids
            )



        # -------------------------------
        # بهینه سازی Query
        # -------------------------------

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

        only_available = request.GET.get(
            "only_available"
        )

        if only_available == "1":
            products = products.filter(inventory__gt=0)


        # -------------------------------
        # مرتب سازی
        # -------------------------------

        sort = request.GET.get(
            "sort",
            "newest"
        )


        if sort == "newest":

            products = products.order_by(
                "-created"
            )


        elif sort == "oldest":

            products = products.order_by(
                "created"
            )


        elif sort == "cheap":

            products = products.order_by(
                "off_price",
                "price"
            )


        elif sort == "expensive":

            products = products.order_by(
                "-off_price",
                "-price"
            )



        # -------------------------------
        # Pagination
        # -------------------------------

        paginator = Paginator(
            products,
            PRODUCTS_PER_PAGE
        )

        page = request.GET.get(
            "page"
        )


        page_obj = paginator.get_page(
            page
        )


        # -------------------------------
        # Wishlist
        # -------------------------------

        if (
            request.user.is_authenticated
            and isinstance(request.user, ShopUser)
        ):

            saved_product_ids = list(
                request.user.saved_products.values_list(
                    "id",
                    flat=True
                )
            )

        else:

            saved_product_ids = []



        # -------------------------------
        # Render محصولات
        # -------------------------------

        html = render_to_string(
            "includes/products_list.html",
            {
                "page_obj": page_obj,
                "products": page_obj.object_list,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "saved_product_ids": saved_product_ids,
            },
            request=request
        )


        return JsonResponse(
            {
                "html": html,
                "count": paginator.count,
            }
        )


class WishlistToggleView(View):

    def post(self, request, product_id):

        product = get_object_or_404(
            Product,
            id=product_id
        )

        # -------------------------
        # کاربر لاگین کرده
        # -------------------------

        if request.user.is_authenticated:

            saved_products = request.user.saved_products

            if saved_products.filter(
                id=product.id
            ).exists():

                saved_products.remove(product)

                status = "removed"

            else:

                saved_products.add(product)

                status = "added"

            wishlist_products = saved_products.all()

        # -------------------------
        # مهمان
        # -------------------------

        else:

            wishlist = get_wishlist(
                request.session
            )

            if product.id in wishlist:

                wishlist.remove(product.id)

                status = "removed"

            else:

                wishlist.append(product.id)

                status = "added"

            save_wishlist(
                request.session,
                wishlist
            )

            wishlist_products = Product.objects.filter(
                id__in=wishlist
            )

        wishlist_count = wishlist_products.count()

        # -------------------------
        # Render dropdown
        # -------------------------

        wishlist_html = render_to_string(
            "includes/wishlist_dropdown_items.html",
            {
                "wishlist_products": wishlist_products,
                "wishlist_count": wishlist_count,
            },
            request=request,
        )

        return JsonResponse({

            "success": True,

            "status": status,

            "product_id": product.id,

            "wishlist_count": wishlist_count,

            "wishlist_html": wishlist_html,

        })
class WishlistView(ListView):
    model = Product
    template_name = "shop/wishlist.html"
    context_object_name = "products"
    paginate_by = PRODUCTS_PER_PAGE

    def get_queryset(self):

        if (
            self.request.user.is_authenticated
            and isinstance(self.request.user, ShopUser)
        ):

            products = (
                self.request.user.saved_products
                .select_related("brand", "category")
                .prefetch_related("images", "variants")
            )

        else:

            wishlist = get_wishlist(self.request.session)

            products = (
                Product.objects.filter(id__in=wishlist)
                .select_related("brand", "category")
                .prefetch_related("images", "variants")
            )

        # -------------------------
        # Category Filter
        # -------------------------
        category_ids = self.request.GET.getlist("categories")

        if category_ids:
            products = products.filter(category__id__in=category_ids)

        # -------------------------
        # Brand Filter
        # -------------------------
        brand_ids = self.request.GET.getlist("brands")

        if brand_ids:
            products = products.filter(brand__id__in=brand_ids)

        # -------------------------
        # Price Filter
        # -------------------------
        min_price = self.request.GET.get("min_price")
        max_price = self.request.GET.get("max_price")

        if min_price:
            products = products.filter(price__gte=min_price)

        if max_price:
            products = products.filter(price__lte=max_price)

        # -------------------------
        # Only Available
        # -------------------------
        if self.request.GET.get("only_available"):
            products = products.filter(is_available=True)

        # -------------------------
        # Ordering
        # -------------------------
        sort = self.request.GET.get("sort", "newest")

        if sort == "newest":
            products = products.order_by("-created")

        elif sort == "oldest":
            products = products.order_by("created")

        elif sort == "cheap":
            products = products.order_by("off_price", "price")

        elif sort == "expensive":
            products = products.order_by("-off_price", "-price")

        return products

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        products = self.object_list

        context["categories"] = (
            Category.objects.filter(product__in=products)
            .distinct()
            .order_by("name")
        )

        context["brands"] = (
            Brand.objects.filter(products__in=products)
            .distinct()
            .order_by("name")
        )

        if (
            self.request.user.is_authenticated
            and isinstance(self.request.user, ShopUser)
        ):
            context["saved_product_ids"] = list(
                self.request.user.saved_products.values_list(
                    "id",
                    flat=True
                )
            )
        else:
            context["saved_product_ids"] = get_wishlist(self.request.session)

        price_range = products.aggregate(
            min_price=Min("price"),
            max_price=Max("price")
        )

        context["min_price"] = self.request.GET.get(
            "min_price",
            price_range["min_price"] or 0
        )

        context["max_price"] = self.request.GET.get(
            "max_price",
            price_range["max_price"] or 0
        )

        context["selected_categories"] = [
            int(x)
            for x in self.request.GET.getlist("categories")
        ]

        context["selected_brands"] = [
            int(x)
            for x in self.request.GET.getlist("brands")
        ]

        context["only_available"] = bool(
            self.request.GET.get("only_available")
        )

        context["current_sort"] = self.request.GET.get(
            "sort",
            "newest"
        )
        context["is_wishlist_page"] = True

        return context


class WishlistAjaxView(WishlistView):

    def get(self, request, *args, **kwargs):

        self.object_list = self.get_queryset()

        context = self.get_context_data()

        html = render_to_string(
            "includes/products_list.html",
            context=context,
            request=request
        )

        return JsonResponse({
            "html": html,
            "count": context["paginator"].count,
        })


class RemoveWishlistItemView(View):

    def post(self, request):

        product_id = request.POST.get("product_id")

        if not product_id:
            return JsonResponse({
                "success": False
            })

        product_id = int(product_id)

        # -------------------------
        # User
        # -------------------------
        if request.user.is_authenticated:

            request.user.saved_products.remove(product_id)

            wishlist_products = (
                request.user.saved_products
                .prefetch_related("images")
                .all()
            )

            wishlist_count = wishlist_products.count()

        # -------------------------
        # Guest
        # -------------------------
        else:

            wishlist = request.session.get("wishlist", [])

            if product_id in wishlist:
                wishlist.remove(product_id)

            request.session["wishlist"] = wishlist
            request.session.modified = True

            wishlist_products = (
                Product.objects
                .filter(id__in=wishlist)
                .prefetch_related("images")
            )

            wishlist_count = len(wishlist)

        # -------------------------
        # Render dropdown html
        # -------------------------
        wishlist_html = render_to_string(
            "includes/wishlist_dropdown_items.html",
            {
                "wishlist_products": wishlist_products,
                "wishlist_count": wishlist_count,
            },
            request=request
        )

        return JsonResponse({

            "success": True,

            "product_id": product_id,

            "wishlist_count": wishlist_count,

            "wishlist_html": wishlist_html,

        })




class BrandDetailView(ListView):

    model = Product
    template_name = "shop/brand_detail.html"
    context_object_name = "products"
    paginate_by = PRODUCTS_PER_PAGE


    def get_queryset(self):

        self.brand = get_object_or_404(
            Brand,
            slug=self.kwargs["slug"]
        )


        products = (
            Product.objects
            .filter(
                brand=self.brand,
                is_available=True
            )
            .select_related(
                "brand",
                "category"
            )
            .prefetch_related(
                "images",
                "variants"
            )
        )


        return products



    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)


        context["brand"] = self.brand


        # برای آیکون سبد خرید
        from cart.cart import Cart

        cart = Cart(self.request)

        context["cart_item_ids"] = [
            int(item["product"].id)
            for item in cart
        ]


        # wishlist
        if self.request.user.is_authenticated:

            context["saved_product_ids"] = list(
                self.request.user.saved_products.values_list(
                    "id",
                    flat=True
                )
            )

        else:

            context["saved_product_ids"] = self.request.session.get(
                "wishlist",
                []
            )

        context["categories"] = (
            Category.objects
            .filter(
                product__brand=self.brand
            )
            .distinct()
            .order_by("name")
        )

        context["brands"] = Brand.objects.filter(
            id=self.brand.id
        )

        context["selected_brands"] = [
            self.brand.id
        ]

        context["selected_categories"] = [
            int(x)
            for x in self.request.GET.getlist("categories")
        ]

        context["only_available"] = (
                self.request.GET.get("only_available") == "1"
                or "only_available" not in self.request.GET
        )

        return context


def search_products(query):

    if not query:
        return Product.objects.none()


    products = Product.objects.filter(
        Q(name__icontains=query)
        |
        Q(description__icontains=query)
        |
        Q(brand__name__icontains=query)
        |
        Q(category__name__icontains=query)
    ).distinct()


    return products


class SearchAjaxView(View):

    def get(self, request):

        query = request.GET.get("q", "").strip()

        if not query:
            return JsonResponse({
                "html": ""
            })


        products = search_products(query)
        print(
            list(
                products.values(
                    "name",
                    "brand__name",
                    "category__name"
                )
            )
        )

        html = ""


        if products.exists():

            for product in products:

                html += f"""
                <div class="search-result-item position-relative border-bottom p-3">

                    <i class="fab fa-sistrix fw-md fs-5 gray-500 d-inline-block"></i>

                    <div class="d-inline-block ms-2">

                        <span class="d-inline-block fw-bold ms-1">
                            {product.name}
                        </span>

                        <span class="d-block">
                            در دسته 
                            <strong>
                                {product.category.name}
                            </strong>
                        </span>

                    </div>


                    <a href="{product.get_absolute_url()}"
                       class="stretched-link">
                    </a>

                </div>
                """


        else:

            html = """
            <div class="p-3 text-center text-muted">
                محصولی پیدا نشد
            </div>
            """


        return JsonResponse({
            "html": html
        })


class SearchResultView(View):

    def get(self, request):

        query = request.GET.get("q", "").strip()

        products = search_products(query)


        # برندهای مرتبط با نتایج سرچ
        brands = Brand.objects.filter(
            products__in=products
        ).distinct()


        # دسته بندی‌های مرتبط با نتایج سرچ
        categories = Category.objects.filter(
            product__in=products
        ).distinct()



        context = {

            "products": products,

            "query": query,

            "brands": brands,

            "categories": categories,

        }


        return render(
            request,
            "shop/search_result.html",
            context
        )


class SearchProductsAjaxView(View):

    def get(self, request):

        query = request.GET.get("q", "").strip()


        # اول سرچ
        products = search_products(query)


        # فقط موجود
        only_available = request.GET.get("only_available")


        if only_available == "1":
            products = products.filter(
                inventory__gt=0
            )


        # دسته بندی
        category_ids = request.GET.getlist("categories")

        if category_ids:
            products = products.filter(
                category_id__in=category_ids
            )


        # برند
        brand_ids = request.GET.getlist("brands")

        if brand_ids:
            products = products.filter(
                brand_id__in=brand_ids
            )


        # قیمت
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


        # مرتب سازی
        sort = request.GET.get(
            "sort",
            "newest"
        )


        if sort == "newest":

            products = products.order_by(
                "-created"
            )


        elif sort == "oldest":

            products = products.order_by(
                "created"
            )


        elif sort == "cheap":

            products = products.order_by(
                "off_price"
            )


        elif sort == "expensive":

            products = products.order_by(
                "-off_price"
            )


        paginator = Paginator(
            products,
            PRODUCTS_PER_PAGE
        )


        page_obj = paginator.get_page(
            request.GET.get("page")
        )


        html = render_to_string(
            "includes/products_list.html",
            {
                "page_obj": page_obj,
                "products": page_obj.object_list,
            },
            request=request
        )


        return JsonResponse({
            "html": html,
            "count": paginator.count
        })


class ProductListAjaxView(View):

    def get(self, request):

        print("PRODUCT LIST AJAX HIT")
        print(request.GET)



        query = request.GET.get("q", "").strip()

        if query:

            products = search_products(query)

        else:

            products = Product.objects.all()


        # -------------------------------
        # فیلتر دسته بندی
        # -------------------------------

        category_ids = request.GET.getlist("categories")


        if category_ids:

            products = products.filter(
                category_id__in=category_ids
            )



        # -------------------------------
        # فیلتر برند
        # -------------------------------

        brand_ids = request.GET.getlist("brands")


        if brand_ids:

            products = products.filter(
                brand_id__in=brand_ids
            )



        # -------------------------------
        # بهینه سازی Query
        # -------------------------------

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
        # قیمت
        # -------------------------------

        min_price = request.GET.get(
            "min_price"
        )

        max_price = request.GET.get(
            "max_price"
        )


        if min_price:

            products = products.filter(
                off_price__gte=min_price
            )


        if max_price:

            products = products.filter(
                off_price__lte=max_price
            )



        # -------------------------------
        # نمایش ناموجودها
        # -------------------------------

        only_available = request.GET.get(
            "only_available"
        )

        if only_available != "0":
            products = products.filter(
                inventory__gt=0
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



        print(
            "FINAL PRODUCTS:",
            list(
                products.values_list(
                    "name",
                    "inventory"
                )
            )
        )



        # -------------------------------
        # مرتب سازی
        # -------------------------------

        sort = request.GET.get(
            "sort",
            "newest"
        )


        if sort == "newest":

            products = products.order_by(
                "-created"
            )


        elif sort == "oldest":

            products = products.order_by(
                "created"
            )


        elif sort == "cheap":

            products = products.order_by(
                "off_price",
                "price"
            )


        elif sort == "expensive":

            products = products.order_by(
                "-off_price",
                "-price"
            )



        # -------------------------------
        # Pagination
        # -------------------------------

        paginator = Paginator(
            products,
            PRODUCTS_PER_PAGE
        )


        page_obj = paginator.get_page(
            request.GET.get("page")
        )



        # -------------------------------
        # Wishlist
        # -------------------------------

        if (
            request.user.is_authenticated
            and isinstance(request.user, ShopUser)
        ):

            saved_product_ids = list(
                request.user.saved_products.values_list(
                    "id",
                    flat=True
                )
            )

        else:

            saved_product_ids = []



        # -------------------------------
        # Render
        # -------------------------------

        html = render_to_string(
            "includes/products_list.html",
            {
                "page_obj": page_obj,
                "products": page_obj.object_list,
                "paginator": paginator,
                "is_paginated": page_obj.has_other_pages(),
                "saved_product_ids": saved_product_ids,
            },
            request=request
        )


        return JsonResponse(
            {
                "html": html,
                "count": paginator.count,
            }
        )


class AddProductCommentView(LoginRequiredMixin, View):

    def post(self, request, product_id):

        product = get_object_or_404(
            Product,
            id=product_id
        )

        title = request.POST.get("title")
        body = request.POST.get("body")

        score = request.POST.get(
            "score",
            5
        )

        # نکات مثبت و منفی آزاد
        positive_points = request.POST.get(
            "positive_points"
        )

        negative_points = request.POST.get(
            "negative_points"
        )

        # --------------------------------
        # بررسی خرید محصول توسط کاربر
        # --------------------------------

        is_buyer = OrderItem.objects.filter(
            order__user=request.user,
            order__paid=True,
            product=product
        ).exists()

        # --------------------------------
        # بررسی ثبت قبلی دیدگاه
        # --------------------------------

        existing_comment = ProductComment.objects.filter(
            user=request.user,
            product=product
        ).first()

        if existing_comment:

            messages.warning(
                request,
                "شما قبلاً برای این محصول دیدگاه ثبت کرده‌اید. "
                "هر کاربر فقط یک دیدگاه برای هر محصول می‌تواند ثبت کند. "
                "برای تغییر دیدگاه خود می‌توانید آن را از پنل کاربری ویرایش کنید."
            )

            return redirect(
                "shop:product_detail",
                id=product.id,
                slug=product.slug
            )

        # --------------------------------
        # ایجاد کامنت
        # --------------------------------

        comment = ProductComment.objects.create(
            product=product,
            user=request.user,
            title=title,
            body=body,
            score=score,
            positive_points=positive_points,
            negative_points=negative_points,
            is_buyer=is_buyer
        )

        # --------------------------------
        # ثبت موضوعات دیدگاه
        # --------------------------------

        for point in CommentPoint.objects.all():

            point_type = request.POST.get(
                f"point_type_{point.id}"
            )

            if point_type in ["positive", "negative"]:

                ProductCommentPoint.objects.create(
                    comment=comment,
                    point=point,
                    point_type=point_type
                )

        return redirect(
            "shop:product_detail",
            id=product.id,
            slug=product.slug
        )


class AddProductQuestionView(LoginRequiredMixin, View):

    def post(self, request, product_id):

        product = get_object_or_404(
            Product,
            id=product_id
        )

        body = request.POST.get("body", "").strip()

        if not body:
            return redirect(
                "shop:product_detail",
                id=product.id,
                slug=product.slug
            )

        ProductQuestion.objects.create(
            product=product,
            user=request.user,
            body=body
        )

        return redirect(
            "shop:product_detail",
            id=product.id,
            slug=product.slug
        )


class AddProductAnswerView(LoginRequiredMixin, View):

    def post(self, request, question_id):

        question = get_object_or_404(
            ProductQuestion,
            id=question_id,
            is_active=True
        )

        body = request.POST.get("body", "").strip()

        if not body:
            return redirect(
                "shop:product_detail",
                id=question.product.id,
                slug=question.product.slug
            )

        # اگر کاربر صاحب فروشگاه/فروشنده محصول باشد
        is_seller = (
            question.product.user == request.user
            if hasattr(question.product, "user")
            else False
        )

        ProductAnswer.objects.create(
            question=question,
            user=request.user,
            body=body,
            is_seller=is_seller
        )

        return redirect(
            "shop:product_detail",
            id=question.product.id,
            slug=question.product.slug
        )


class EditProductCommentView(LoginRequiredMixin, View):

    def get(self, request, comment_id):

        comment = get_object_or_404(
            ProductComment,
            id=comment_id,
            user=request.user
        )

        points = {}

        for relation in comment.comment_points.select_related("point"):

            points[str(relation.point.id)] = relation.point_type


        return JsonResponse({
            "success": True,
            "comment": {
                "id": comment.id,
                "product_id": comment.product.id,
                "product_name": comment.product.name,
                "title": comment.title,
                "body": comment.body,
                "score": comment.score,
                "positive_points": comment.positive_points or "",
                "negative_points": comment.negative_points or "",
                "points": points,
            }
        })


    def post(self, request, comment_id):

        comment = get_object_or_404(
            ProductComment,
            id=comment_id,
            user=request.user
        )


        title = request.POST.get(
            "title",
            ""
        ).strip()


        body = request.POST.get(
            "body",
            ""
        ).strip()


        score = request.POST.get(
            "score",
            5
        )


        positive_points = request.POST.get(
            "positive_points",
            ""
        ).strip()


        negative_points = request.POST.get(
            "negative_points",
            ""
        ).strip()



        if not title or not body:

            return JsonResponse({
                "success": False,
                "message": "عنوان و متن دیدگاه الزامی است."
            }, status=400)



        try:

            score = int(score)

        except (TypeError, ValueError):

            score = 5



        if score < 1 or score > 5:

            return JsonResponse({
                "success": False,
                "message": "امتیاز باید بین ۱ تا ۵ باشد."
            }, status=400)



        # -----------------------------
        # بروزرسانی کامنت
        # -----------------------------

        comment.title = title
        comment.body = body
        comment.score = score
        comment.positive_points = positive_points
        comment.negative_points = negative_points

        comment.save()



        # -----------------------------
        # بروزرسانی موضوعات
        # -----------------------------

        ProductCommentPoint.objects.filter(
            comment=comment
        ).delete()



        for point in CommentPoint.objects.all():

            point_type = request.POST.get(
                f"point_type_{point.id}"
            )


            if point_type in [
                "positive",
                "negative"
            ]:

                ProductCommentPoint.objects.create(
                    comment=comment,
                    point=point,
                    point_type=point_type
                )



        # -----------------------------
        # پیام جنگو
        # -----------------------------

        messages.success(
            request,
            "دیدگاه شما با موفقیت ویرایش شد."
        )


        return JsonResponse({
            "success": True
        })


class BestSellingProductsView(ListView):

    model = Product

    template_name = "shop/best_selling.html"

    context_object_name = "products"

    paginate_by = PRODUCTS_PER_PAGE


    def get_queryset(self):

        products = (
            Product.objects
            .filter(
                is_available=True
            )
            .annotate(
                total_sold=Sum(
                    "orders__quantity"
                )
            )
            .filter(
                total_sold__isnull=False
            )
            .prefetch_related(
                "images",
                "variants"
            )
            .select_related(
                "brand",
                "category"
            )
            .order_by(
                "-total_sold"
            )
        )


        # -------------------------
        # Price Filter
        # -------------------------

        min_price = self.request.GET.get(
            "min_price"
        )

        max_price = self.request.GET.get(
            "max_price"
        )


        if min_price:
            products = products.filter(
                price__gte=min_price
            )


        if max_price:
            products = products.filter(
                price__lte=max_price
            )


        # -------------------------
        # Brand Filter
        # -------------------------

        brand_ids = self.request.GET.getlist(
            "brands"
        )


        if brand_ids:

            products = products.filter(
                brand__id__in=brand_ids
            )


        # -------------------------
        # Sorting
        # -------------------------

        sort = self.request.GET.get(
            "sort"
        )


        if sort == "cheap":

            products = products.order_by(
                "off_price",
                "price"
            )


        elif sort == "expensive":

            products = products.order_by(
                "-off_price",
                "-price"
            )


        elif sort == "newest":

            products = products.order_by(
                "-created"
            )


        return products
    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)



        context["categories"] = Category.objects.all().order_by(
            "name"
        )


        context["brands"] = Brand.objects.all().order_by(
            "name"
        )



        if self.request.user.is_authenticated:

            context["saved_product_ids"] = list(

                self.request.user.saved_products.values_list(
                    "id",
                    flat=True
                )

            )

        else:

            context["saved_product_ids"] = self.request.session.get(
                "wishlist",
                []
            )




        cart = Cart(
            self.request
        )


        context["cart_item_ids"] = [

            int(item["product"].id)

            for item in cart

        ]



        products = self.get_queryset()



        context["min_price"] = self.request.GET.get(
            "min_price",
            products.order_by("price").first().price
            if products.exists()
            else 0
        )


        context["max_price"] = self.request.GET.get(
            "max_price",
            products.order_by("-price").first().price
            if products.exists()
            else 0
        )



        context["selected_brands"] = [

            int(x)

            for x in self.request.GET.getlist(
                "brands"
            )

        ]



        context["selected_categories"] = []



        context["only_available"] = True

        context["current_sort"] = self.request.GET.get(
            "sort",
            "best"
        )


        context["is_wishlist_page"] = False



        return context


class BestSellingProductsAjaxView(View):

    def get(self, request, *args, **kwargs):

        products = (
            Product.objects
            .filter(
                is_available=True
            )
            .annotate(
                sales_count=Sum(
                    "orders__quantity"
                )
            )
            .filter(
                sales_count__gt=0
            )
            .select_related(
                "brand",
                "category"
            )
            .prefetch_related(
                "images",
                "variants"
            )
        )

        # =========================
        # Category
        # =========================

        category_ids = request.GET.getlist(
            "categories"
        )

        if category_ids:

            products = products.filter(
                category__id__in=category_ids
            )


        # =========================
        # Brand
        # =========================

        brand_ids = request.GET.getlist(
            "brands"
        )

        if brand_ids:

            products = products.filter(
                brand__id__in=brand_ids
            )


        # =========================
        # Price
        # =========================

        min_price = request.GET.get(
            "min_price"
        )

        max_price = request.GET.get(
            "max_price"
        )


        if min_price:

            products = products.filter(
                price__gte=min_price
            )


        if max_price:

            products = products.filter(
                price__lte=max_price
            )


        # =========================
        # Available
        # =========================

        only_available = request.GET.get(
            "only_available"
        )


        if only_available == "1":

            products = products.filter(
                inventory__gt=0,
                is_available=True
            )


        # =========================
        # Ordering
        # =========================

        sort = request.GET.get(
            "sort",
            "best"
        )

        if sort == "cheap":

            products = products.order_by(
                "off_price",
                "price",
                "-sales_count"
            )


        elif sort == "expensive":

            products = products.order_by(
                "-off_price",
                "-price",
                "-sales_count"
            )

        elif sort == "newest":

            products = products.order_by(

                "-created",

                "-sales_count"

            )

        elif sort == "oldest":

            products = products.order_by(

                "created",

                "-sales_count"

            )

        elif sort == "cheap":

            products = products.order_by(

                "off_price",

                "-sales_count"

            )

        elif sort == "expensive":

            products = products.order_by(

                "-off_price",

                "-sales_count"

            )

        else:


            products = products.order_by(

                "-sales_count"

            )
        print(products.count())
        print(list(products.values("id", "name", "sales_count")))
        # =========================
        # Pagination
        # =========================

        paginator = Paginator(
            products,
            PRODUCTS_PER_PAGE
        )


        page_number = request.GET.get(
            "page",
            1
        )


        page_obj = paginator.get_page(
            page_number
        )


        # =========================
        # Context
        # =========================

        context = {

            "products": page_obj.object_list,

            "page_obj": page_obj,

            "paginator": paginator,

            "is_paginated": page_obj.has_other_pages(),

            "saved_product_ids": (
                    list(
                        request.user.saved_products.values_list(
                            "id",
                            flat=True
                        )
                    )
                    if request.user.is_authenticated
                    else request.session.get(
                        "wishlist",
                        []
                    )
                ),
            "is_wishlist_page": False,

        }


        from cart.cart import Cart

        cart = Cart(request)


        context["cart_item_ids"] = [

            int(item["product"].id)

            for item in cart

        ]


        html = render_to_string(
            "includes/products_list.html",
            context,
            request=request
        )


        return JsonResponse({

            "html": html,

            "count": paginator.count,

        })