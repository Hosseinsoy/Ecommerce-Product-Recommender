from django.urls import path

from order import views
from account.views import login_choice

app_name = 'order'

urlpatterns = [
    path('', views.order, name='order'),
    path('create/', views.create_order, name='create_order'),
    path('register/', views.shopping_register, name='shopping_register'),
    path('v+erification-code/', views.shopping_register_verification_code, name='shopping_register_verification_code'),
    path('login/', login_choice, name='login_choice'),
    path('invoice_pdf/<int:order_id>', views.invoice_pdf, name='invoice_pdf'),
    path('return-order/<int:order_id>', views.return_order, name='return_order'),
    path('return-product/<int:order_id>', views.return_product, name='return_product'),
    path('show-returns/<int:order_id>', views.show_returns, name='show_returns'),
    path('payment-successful/<int:order_id>', views.payment_successful, name='payment_successful'),
    path(
        'cancel/<int:order_id>/',
        views.cancel_order,
        name='cancel_order'
    ),

]