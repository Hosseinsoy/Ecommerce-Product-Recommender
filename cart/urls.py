from django.urls import path
import cart.views as views

app_name = 'cart'

urlpatterns = [
    path('add/<int:product_id>', views.add_to_cart, name='add_to_cart'),
    path('detail/', views.cart_detail, name='cart_detail'),
    path('update-quantity/', views.update_quantity, name='update_quantity'),
    path('remove-item', views.remove_item, name='remove_item'),
    path("toggle/<int:product_id>/", views.CartToggleView.as_view(), name="cart_toggle")
]