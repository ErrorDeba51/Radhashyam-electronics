# radhashyam/cart/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name=_('user')
    )
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_('created at'))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_('updated at'))
    is_active = models.BooleanField(
        default=True, verbose_name=_('active status'))

    class Meta:
        verbose_name = _('shopping cart')
        verbose_name_plural = _('shopping carts')

    @property
    def total(self):
        """Calculate total using generator expression for better performance"""
        return sum(item.total_price for item in self.items.all())

    @property
    def item_count(self):
        """Get total quantity of all items in cart"""
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    def clear(self):
        """Soft delete cart by marking inactive and removing items"""
        self.is_active = False
        self.save()
        self.items.all().delete()

    def __str__(self):
        return f"{self.user.email}'s Cart ({self.item_count} items)"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('cart')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        verbose_name=_('product')
    )
    quantity = models.PositiveIntegerField(
        default=1, verbose_name=_('quantity'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cart', 'product')
        verbose_name = _('cart item')
        verbose_name_plural = _('cart items')

    @property
    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.product.title} (${self.total_price})"
