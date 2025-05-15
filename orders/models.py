# radhashyam/orders/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
from products.models import Product
import random

User = get_user_model()


class Pincode(models.Model):
    code = models.CharField(
        max_length=6,
        unique=True,
        verbose_name=_('Pincode'),
        help_text=_('6-digit postal code')
    )
    delivery_days = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Delivery Days'),
        help_text=_('Estimated delivery time in days')
    )
    cod_advance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('COD Advance'),
        help_text=_('Advance payment required for COD orders')
    )
    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Delivery Charge'),
        help_text=_('Shipping cost for this pincode')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active'),
        help_text=_('Enable/disable serviceability')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Serviceable Pincode')
        verbose_name_plural = _('Serviceable Pincodes')
        ordering = ['code']
        indexes = [models.Index(fields=['code'])]

    def __str__(self):
        return f"{self.code} ({self.delivery_days} days delivery)"

    def formatted_cod_advance(self):
        return "Free" if self.cod_advance == 0 else f"₹{self.cod_advance:.2f}"

    def formatted_delivery_charge(self):
        return "Free" if self.delivery_charge == 0 else f"₹{self.delivery_charge:.2f}"


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Pending Payment')),
        ('confirmed', _('Order Confirmed')),
        ('processing', _('Processing')),
        ('shipped', _('Shipped')),
        ('out_for_delivery', _('Out for Delivery')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('failed', _('Payment Failed')),
    ]

    PAYMENT_CHOICES = [
        ('cod', _('Cash on Delivery')),
        ('razorpay', _('Online Payment')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('Customer')
    )
    product_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_('Product Subtotal')
    )
    delivery_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('Delivery Cost')
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name=_('Order Total')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Order Status')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        verbose_name=_('Payment Method')
    )
    delivery_date = models.DateField(
        verbose_name=_('Expected Delivery')
    )
    pincode = models.CharField(
        max_length=6,
        verbose_name=_('Delivery Pincode')
    )
    address = models.TextField(
        verbose_name=_('Complete Shipping Address')
    )
    phone = models.CharField(
        max_length=15,
        verbose_name=_('Contact Phone'),
        blank=True
    )
    razorpay_order_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Razorpay Order ID')
    )
    payment_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Payment Transaction ID')
    )
    cod_advance_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_('COD Advance Paid')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cancellation Reason')
    )
    feedback_rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Feedback Rating'),
        help_text=_('Customer rating from 1-5')
    )
    feedback_comments = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Feedback Comments'),
        help_text=_('Customer comments about the order')
    )
    feedback_submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Feedback Submission Time')
    )
    delivery_otp = models.CharField(
        max_length=6,
        blank=True,
        null=True,
        verbose_name=_('Delivery OTP'),
        help_text=_('OTP for delivery confirmation')
    )

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'delivery_date']),
            models.Index(fields=['pincode']),
        ]

    def __str__(self):
        return f"Order #{self.id} - {self.user.email} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        """Generate OTP when status changes to out_for_delivery"""
        if self.pk:
            original = Order.objects.get(pk=self.pk)
            if original.status != self.status and self.status == 'out_for_delivery':
                self.delivery_otp = ''.join(random.choices('0123456789', k=6))
        else:
            if self.status == 'out_for_delivery':
                self.delivery_otp = ''.join(random.choices('0123456789', k=6))
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return self.items.aggregate(total=models.Sum('quantity'))['total'] or 0

    @property
    def remaining_amount(self):
        if self.payment_method == 'cod':
            return max(self.total_amount - self.cod_advance_paid, Decimal('0.00'))
        return Decimal('0.00')

    def formatted_delivery_charge(self):
        return "Free" if self.delivery_charge == 0 else f"₹{self.delivery_charge:.2f}"

    def formatted_cod_advance(self):
        return "Free" if self.cod_advance_paid == 0 else f"₹{self.cod_advance_paid:.2f}"

    def has_feedback(self):
        return self.feedback_rating is not None

    def get_feedback_rating_display(self):
        ratings = {
            1: 'Very Poor',
            2: 'Poor',
            3: 'Average',
            4: 'Good',
            5: 'Excellent'
        }
        return ratings.get(self.feedback_rating, 'Not rated')

    def generate_delivery_otp(self):
        self.delivery_otp = ''.join(random.choices('0123456789', k=6))
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Parent Order')
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name=_('Product Variant')
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Purchased Quantity')
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Unit Price at Purchase')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        ordering = ['-created_at']
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.quantity}x {self.product.title} @ ₹{self.price}"

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    @property
    def total_price(self):
        return self.quantity * self.price


class DeliveryAgent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='delivery_agent',
        verbose_name=_('System Account')
    )
    service_areas = models.ManyToManyField(
        Pincode,
        related_name='agents',
        verbose_name=_('Serviced Pincodes')
    )
    phone_number = models.CharField(
        max_length=15,
        verbose_name=_('Primary Contact Number')
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Available for Assignments')
    )
    current_location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Last Known Location')
    )
    vehicle_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Vehicle Registration')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Delivery Agent')
        verbose_name_plural = _('Delivery Agents')
        ordering = ['-is_available', 'user__email']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.phone_number})"

    @property
    def service_areas_str(self):
        return ", ".join(self.service_areas.values_list('code', flat=True))


class DeliveryAssignment(models.Model):
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery_assignment',
        verbose_name=_('Assigned Order')
    )
    agent = models.ForeignKey(
        DeliveryAgent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments',
        verbose_name=_('Responsible Agent')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Delivery Instructions')
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Delivery Assignment')
        verbose_name_plural = _('Delivery Assignments')
        ordering = ['-assigned_at']

    def __str__(self):
        return f"Delivery #{self.id} for Order {self.order_id}"

    def save(self, *args, **kwargs):
        if not self.agent and self.order.pincode:
            self.agent = DeliveryAgent.objects.filter(
                service_areas__code=self.order.pincode,
                is_available=True
            ).first()
        super().save(*args, **kwargs)

    @property
    def delivery_status(self):
        return self.order.get_status_display()
