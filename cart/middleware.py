# radhashyam/cart/middleware.py

from django.utils.deprecation import MiddlewareMixin


class InventoryCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request, 'cart'):
            for item in request.cart.items.all():
                if item.product.stock < item.quantity:
                    messages.warning(request,
                                     f"Only {item.product.stock} units available for {item.product.title}")
                    item.quantity = item.product.stock
                    item.save()
        return self.get_response(request)


# radhashyam/cart/middleware.py


class CartMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            request.cart = request.user.cart
            request.session['cart_count'] = request.cart.items.count()
        else:
            request.session['cart_count'] = 0
