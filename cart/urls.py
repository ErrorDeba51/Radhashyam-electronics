# radhashyam/cart/urls.py

from django.urls import path
from .views import cart_view, update_cart, add_to_cart, remove_from_cart, clear_cart
app_name = 'cart'
urlpatterns = [
    path('', cart_view, name='cart_view'),
    path('add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('update/<int:product_id>/', update_cart, name='update_cart'),
    path('remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('clear/', clear_cart, name='clear_cart'),
]
