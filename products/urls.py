# radhashyam/products/urls.py

from django.urls import path
from .views import home, product_detail, category_view, advanced_search, appliance_view

urlpatterns = [
    path('', home, name='home'),
    path('search/', advanced_search, name='advanced_search'),
    path('category/<str:category>/', category_view, name='category'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('appliance/', appliance_view, name='appliance'),

]
