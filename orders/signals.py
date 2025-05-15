# radhashyam/orders/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Order  # Ensure models are imported


@receiver(post_save, sender=Order)
def send_order_status_update(sender, instance, **kwargs):
    """Send email when order status changes"""
    if instance.tracker.has_changed('status'):  # Verify tracker is properly configured
        subject = f"Order {instance.id} Status Update"
        message = f"""Your order status has been updated to: {instance.get_status_display()}
Expected Delivery Date: {instance.delivery_date}"""

        if instance.status == 'out_for_delivery':
            message += f"\nDelivery Agent Contact: {instance.delivery_boy_contact}"

        send_mail(
            subject,
            message,
            'orders@radhashyam.com',
            [instance.user.email],
            fail_silently=False,
        )


@receiver(post_save, sender=ProductReview)
def notify_review_posted(sender, instance, created, **kwargs):
    """Notify admin when new review is posted"""
    if created:
        send_mail(
            'New Product Review Posted',
            f'A new review was posted for {instance.product.title}',
            'reviews@radhashyam.com',
            ['admin@radhashyam.com'],
            fail_silently=False,
        )
