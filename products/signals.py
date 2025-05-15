# radhashyam/products/signals.py

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver


@receiver(pre_save, sender=Product)
def track_stock_changes(sender, instance, **kwargs):
    if instance.pk:
        original = Product.objects.get(pk=instance.pk)
        if original.stock != instance.stock:
            StockUpdate.objects.create(
                product=instance,
                old_stock=original.stock,
                new_stock=instance.stock,
                changed_by=getattr(instance, '_current_user', None)
            )


@receiver(post_save, sender=StockUpdate)
def check_low_stock(sender, instance, **kwargs):
    inventory = Inventory.objects.get(product=instance.product)
    if inventory.stock_status == 'low_stock' and inventory.is_auto_restock:
        # Trigger restocking workflow
        send_low_stock_alert(instance.product)
