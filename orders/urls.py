# radhashyam/orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/<int:order_id>/', views.checkout, name='checkout_with_order'),

    path('create/<int:product_id>/', views.create_order,
         name='create_direct_order'),

    path('tracking/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('history/', views.purchase_history, name='order_history'),

    path('invoice/<int:order_id>/',
         views.download_invoice, name='download_invoice'),

    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),

    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),

    path('feedback/<int:order_id>/', views.submit_feedback, name='submit_feedback'),

    path('api/check-pincode/', views.check_pincode, name='check_pincode'),
]
