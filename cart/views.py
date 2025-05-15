# radhashyam/cart/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from products.models import Product
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Cart, CartItem


@require_POST
@login_required
def add_to_cart(request, product_id):
    """Add product to cart with default quantity"""
    product = get_object_or_404(Product, id=product_id)

    cart_item, created = CartItem.objects.get_or_create(
        cart=request.user.cart,
        product=product
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart:cart_view')


@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/view.html', {'cart': cart})


@require_POST
@login_required
def update_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.user.cart
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )
    cart_item.quantity = max(1, min(quantity, product.stock))
    cart_item.save()

    return JsonResponse({
        'success': True,
        'total': cart.total,
        'cart_count': cart.items.count(),
        'quantity': cart_item.quantity
    })


@require_POST
@login_required
def remove_from_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.user.cart
    deleted_count, _ = CartItem.objects.filter(
        cart=cart, product=product).delete()

    return JsonResponse({
        'success': deleted_count > 0,
        'total': cart.total,
        'cart_count': cart.items.count()
    })


@require_POST
@login_required
def clear_cart(request):
    cart = request.user.cart
    deleted_count, _ = CartItem.objects.filter(cart=cart).delete()
    return JsonResponse({
        'success': deleted_count > 0,
        'total': 0,
        'cart_count': 0
    })
