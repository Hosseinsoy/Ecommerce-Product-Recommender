from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('products', views.ProductViewSet)

app_name = 'api'

urlpatterns = [
    # path('products/', views.ProductListAPIView.as_view(), name='products-list_api'),
    # path('product/<pk>/', views.ProductDetailAPIView.as_view(), name='product-detail_api'),
    path('users/', views.ShopUserListAPIView.as_view(), name='user-list_api'),
    path('register/', views.ShopUserRegisterAPIView.as_view(), name='user-register_api'),
    path('', include(router.urls)),
]