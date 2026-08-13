from .models import Category
from account.models import ShopUser
from shop.models import Product
from shop.utils.wishlist import get_wishlist
from account.models import ShopUser
from shop.utils.wishlist import wishlist_count


def categories(request):
    return {
        'categories': Category.objects.all(),
        'home_categories': Category.objects.filter(id__lte=11)
    }


def wishlist(request):

    if request.user.is_authenticated and isinstance(request.user, ShopUser):
        count = request.user.saved_products.count()
    else:
        count = wishlist_count(request.session)

    return {
        "wishlist_count": count
    }


def wishlist_context(request):

    if (
        request.user.is_authenticated
        and isinstance(request.user, ShopUser)
    ):

        wishlist_products = (
            request.user.saved_products
            .prefetch_related("images")
            .order_by("-id")[:3]
        )

        wishlist_count = request.user.saved_products.count()

    else:

        wishlist = get_wishlist(request.session)

        wishlist_products = (
            Product.objects.filter(id__in=wishlist)
            .prefetch_related("images")[:3]
        )

        wishlist_count = len(wishlist)

    return {
        "wishlist_products": wishlist_products,
        "wishlist_count": wishlist_count,
    }