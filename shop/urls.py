from django.urls import path
import shop.views as views
from .views import ProductListView

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', ProductListView.as_view() , name='product_list'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('save-product/<int:product_id>', views.save_product, name='save_product'),
    path('add-discount-code/', views.add_discount_code, name='add_discount_code'),
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("ajax/category-brands/", views.CategoryBrandsAjaxView.as_view(), name="category_brands"),
    path(
        "category/<slug:slug>/ajax/",
        views.CategoryProductsAjaxView.as_view(),
        kwargs={
            "type": "category"
        },
        name="category_products_ajax"
    ),
    path("wishlist/toggle/<int:product_id>/", views.WishlistToggleView.as_view(), name="wishlist_toggle"),
    path("wishlist/", views.WishlistView.as_view(), name="wishlist"),
    path("wishlist/ajax/", views.WishlistAjaxView.as_view(), name="wishlist_ajax"),
    path("wishlist/remove/", views.RemoveWishlistItemView.as_view(), name="remove_wishlist_item"),
    path(
        "brand/<slug:slug>/ajax/",
        views.CategoryProductsAjaxView.as_view(),
        kwargs={
            "type": "brand"
        },
        name="brand_products_ajax"
    ),
    path("brand/<slug:slug>/", views.BrandDetailView.as_view(), name="brand_products"),
    path(
        "products/ajax/",
        views.ProductListAjaxView.as_view(),
        name="products_ajax"
    ),
    path(
        "search/ajax/",
        views.SearchAjaxView.as_view(),
        name="search_ajax"
    ),
    path(
        "search-result/",
        views.SearchResultView.as_view(),
        name="search"
    ),

    path(
        "search-result/ajax/",
        views.SearchProductsAjaxView.as_view(),
        name="search_products_ajax"
    ),

    path(
        "product/<int:product_id>/comment/add/",
        views.AddProductCommentView.as_view(),
        name="add_product_comment"
    ),
    path(
        "product/<int:product_id>/question/add/",
        views.AddProductQuestionView.as_view(),
        name="add_product_question"
    ),

    path(
        "question/<int:question_id>/answer/add/",
        views.AddProductAnswerView.as_view(),
        name="add_product_answer"
    ),
    path(
        "edit-product-comment/<int:comment_id>/",
        views.EditProductCommentView.as_view(),
        name="edit_product_comment"
    ),
    path(
        "best-selling/",
        views.BestSellingProductsView.as_view(),
        name="best_selling"
    ),
    path(
        "best-selling/ajax/",
        views.BestSellingProductsAjaxView.as_view(),
        name="best_selling_ajax"
    ),
]

