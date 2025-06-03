from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth import views as auth_views
app_name = 'account'

urlpatterns = [
    path('login/', views.login_choice, name='login_choice'),
    path('login/<shopping>', views.login_choice, name='shopping_login_choice'),
    path('login/verification/', views.verification_login, name='verification_login'),
    path('login/verification/code/', views.verification_code, name='verification_code'),
    path('login/username-password/', views.username_password_login, name='username_password_login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('register/verification/', views.register_verification_code, name='register_verification_code'),
    path('profile/', views.profile, name='profile'),
    path('profile/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('create_address/', views.create_address, name='create_address'),
    path('profile/addresses/create_address/', views.create_address_from_profile, name='create_address_from_profile'),
    path('load_cities/', views.load_cities, name='load_cities'),
    path('regenerate-code/', views.regenerate_verification_code, name='regenerate_verification_code'),
    path('clear-verification-code/', views.clear_verification_code, name='clear_verification_code'),
    path('login/seller/', views.login_seller, name='login_seller'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-phone/', views.change_phone, name='change_phone'),
    path('profile/change-phone/code/', views.change_phone_code, name='change_phone_code'),
    path('profile/edit/password-change/', views.CustomPasswordChangeView.as_view(), name='password_change'),
    path('profile/addresses/', views.addresses, name='addresses'),
    path('profile/addresses/remove/', views.remove_address, name='remove_address'),
    path('profile/seller/', views.seller_profile, name='seller_profile'),
    path('profile/seller/products/', views.seller_products, name='seller_products'),
    path('profile/seller/products/add/', views.add_product, name='add_product'),
    path('profile/seller/products/edit/<int:product_id>', views.edit_product, name='edit_product'),
    path('profile/seller/products/make-available', views.make_available, name='make_available'),
    path('profile/seller/products/make-unavailable', views.make_unavailable, name='make_unavailable'),
]