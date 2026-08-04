from django.urls import path
import shop.views as views
from .views import ProductListView

app_name = 'shop'

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', ProductListView.as_view() , name='product_list'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
    path('search-result/', views.search, name='search'),
    path('save-product/<int:product_id>', views.save_product, name='save_product'),
    path('add-discount-code/', views.add_discount_code, name='add_discount_code'),
    path('brand-detail/<slug:slug>/', views.brand_detail, name='brand_detail'),
    path("category/<slug:slug>/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("ajax/category-brands/", views.CategoryBrandsAjaxView.as_view(), name="category_brands"),
    path("category/<slug:slug>/ajax/", views.CategoryProductsAjaxView.as_view(), name="category_products_ajax"),

]