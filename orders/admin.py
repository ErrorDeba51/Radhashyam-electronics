# radhashyam/orders/admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.contrib import messages
from .models import Order, Pincode, DeliveryAgent, DeliveryAssignment, OrderItem
import random

User = get_user_model()


class OrderAdminForm(forms.ModelForm):
    delivery_otp = forms.CharField(
        required=False,
        label='Delivery OTP',
        help_text="Required when marking as Delivered",
        widget=forms.TextInput(attrs={'autocomplete': 'off'}))

    class Meta:
        model = Order
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.status != 'out_for_delivery':
            self.fields['delivery_otp'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        existing_status = self.instance.status if self.instance else None

        # OTP validation for delivery
        if status == 'delivered' and existing_status != 'delivered':
            entered_otp = cleaned_data.get('delivery_otp', '')
            stored_otp = self.instance.delivery_otp if self.instance else None

            if not entered_otp:
                self.add_error(
                    'delivery_otp', 'OTP is required for delivery confirmation')
            elif entered_otp != stored_otp:
                self.add_error(
                    'delivery_otp', 'Invalid OTP. Please check with the customer')

        return cleaned_data


@admin.register(Pincode)
class PincodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'delivery_days',
                    'formatted_cod_advance', 'is_active')
    list_editable = ('delivery_days', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code',)
    ordering = ('code',)
    actions = ['activate_pincodes', 'deactivate_pincodes']

    def formatted_cod_advance(self, obj):
        return "Free" if obj.cod_advance == 0 else f"₹{obj.cod_advance}"
    formatted_cod_advance.short_description = 'COD Advance'

    def activate_pincodes(self, request, queryset):
        queryset.update(is_active=True)
    activate_pincodes.short_description = "Activate selected pincodes"

    def deactivate_pincodes(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_pincodes.short_description = "Deactivate selected pincodes"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'total_price')
    search_fields = ('order__id', 'product__title')
    autocomplete_fields = ('order', 'product')

    def total_price(self, obj):
        return f"₹{obj.quantity * obj.price:.2f}"
    total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
    fieldsets = (
        ('Order Details', {
            'fields': (
                'user',
                'total_amount',
                'payment_method',
                'razorpay_order_id',
                'payment_id',
                'delivery_otp'
            )
        }),
        ('Delivery Info', {
            'fields': (
                'delivery_date',
                'pincode',
                'address',
                'phone',
                'status',
                'cancellation_reason'
            )
        }),
        ('COD Details', {
            'fields': ('cod_advance_paid', 'delivery_charge'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    list_display = (
        'id',
        'user',
        'payment_status',
        'formatted_total',
        'status',
        'formatted_delivery_date',
        'pincode_link',
        'delivery_agent_info',
        'otp_display'
    )
    list_filter = ('status', 'payment_method', 'delivery_date')
    search_fields = ('user__email', 'pincode', 'address',
                     'razorpay_order_id', 'phone')
    autocomplete_fields = ('user',)
    list_per_page = 30
    readonly_fields = ('created_at', 'updated_at')
    actions = ['cancel_orders', 'mark_out_for_delivery',
               'generate_otp_for_selected']
    date_hierarchy = 'created_at'

    def payment_status(self, obj):
        method = obj.get_payment_method_display()
        if obj.payment_method == 'cod':
            return format_html(
                "{}<br>COD Advance Paid: ₹{}<br>Delivery Charge: ₹{}<br>Remaining Balance: ₹{}",
                method,
                obj.cod_advance_paid,
                obj.delivery_charge,
                obj.remaining_amount
            )
        return format_html("{}<br>Delivery Charge: ₹{}", method, obj.delivery_charge)
    payment_status.short_description = 'Payment Details'

    def formatted_total(self, obj):
        base = f"₹{obj.product_total:.2f}"
        delivery = obj.formatted_delivery_charge()
        total = f"₹{obj.total_amount:.2f}"
        return format_html("{} + {} = {}", base, delivery, total)
    formatted_total.short_description = 'Amount Breakdown'

    def formatted_delivery_date(self, obj):
        return obj.delivery_date.strftime("%d %b %Y")
    formatted_delivery_date.short_description = 'Delivery Date'
    formatted_delivery_date.admin_order_field = 'delivery_date'

    def pincode_link(self, obj):
        return format_html('<a href="/admin/orders/pincode/{}/change/">{}</a>', obj.pincode, obj.pincode)
    pincode_link.short_description = 'Pincode Details'

    def delivery_agent_info(self, obj):
        if hasattr(obj, 'delivery_assignment') and obj.delivery_assignment.agent:
            agent = obj.delivery_assignment.agent
            return format_html("{}<br>{}<br>{}",
                               agent.user.get_full_name() or agent.user.email,
                               agent.phone_number,
                               agent.vehicle_number or "No vehicle"
                               )
        return "Not assigned"
    delivery_agent_info.short_description = 'Delivery Agent'

    def otp_display(self, obj):
        if obj.status == 'out_for_delivery':
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                obj.delivery_otp or 'Not Generated'
            )
        return "N/A"
    otp_display.short_description = 'Delivery OTP'

    def save_model(self, request, obj, form, change):
        is_new = not obj.pk
        if change and not is_new:
            original = Order.objects.get(pk=obj.pk)

            if original.status != obj.status and obj.status == 'out_for_delivery':
                obj.generate_delivery_otp()

            if obj.status == 'delivered' and original.status != 'delivered':
                obj.delivery_otp = None

        super().save_model(request, obj, form, change)

    def generate_otp_for_selected(self, request, queryset):
        updated = 0
        for order in queryset.filter(status='out_for_delivery'):
            order.generate_delivery_otp()
            updated += 1
        self.message_user(
            request,
            f"Generated new OTP for {updated} orders",
            messages.SUCCESS if updated else messages.WARNING
        )
    generate_otp_for_selected.short_description = "Regenerate OTP for selected orders"

    def cancel_orders(self, request, queryset):
        allowed_statuses = ['pending', 'confirmed']
        cancellable = queryset.filter(status__in=allowed_statuses)

        for order in cancellable:
            order.status = 'cancelled'
            order.save()

        self.message_user(request,
                          f"Cancelled {cancellable.count()} of {queryset.count()} orders",
                          messages.WARNING if cancellable.count() < queryset.count() else messages.SUCCESS
                          )
    cancel_orders.short_description = "Cancel eligible orders"

    def mark_out_for_delivery(self, request, queryset):
        updated = queryset.filter(status='shipped').update(
            status='out_for_delivery')
        for order in queryset.filter(status='out_for_delivery'):
            order.generate_delivery_otp()
        self.message_user(request,
                          f"{updated} orders marked as Out for Delivery with OTP generated",
                          messages.SUCCESS
                          )
    mark_out_for_delivery.short_description = "Mark shipped as Out for Delivery"


@admin.register(DeliveryAgent)
class DeliveryAgentAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone_number',
        'vehicle_number',
        'service_areas_list',
        'is_available',
        'current_location',
        'updated_at_display'
    )
    list_filter = ('is_available', 'service_areas')
    search_fields = ('user__username', 'phone_number', 'vehicle_number')
    filter_horizontal = ('service_areas',)
    readonly_fields = ('updated_at', 'created_at')
    list_editable = ('is_available', 'current_location', 'vehicle_number')
    fields = (
        'user',
        'phone_number',
        'service_areas',
        'vehicle_number',
        'is_available',
        'current_location',
        'created_at',
        'updated_at'
    )

    def service_areas_list(self, obj):
        return format_html("<ul style='columns:2; margin:0;'>{}</ul>",
                           "".join(
                               f"<li>{p.code} ({p.delivery_days}d)</li>" for p in obj.service_areas.all())
                           )
    service_areas_list.short_description = 'Service Areas'

    def updated_at_display(self, obj):
        return obj.updated_at.strftime("%Y-%m-%d %H:%M")
    updated_at_display.short_description = 'Last Updated'


@admin.register(DeliveryAssignment)
class DeliveryAssignmentAdmin(admin.ModelAdmin):
    list_display = ('order', 'agent_with_contact',
                    'assigned_at', 'delivery_status')
    list_filter = ('assigned_at', 'agent')
    search_fields = ('order__id', 'agent__user__username')
    raw_id_fields = ('order', 'agent')

    def agent_with_contact(self, obj):
        if obj.agent:
            return format_html("{}<br>{}",
                               obj.agent.user.get_full_name() or obj.agent.user.email,
                               obj.agent.phone_number
                               )
        return "Not assigned"
    agent_with_contact.short_description = 'Assigned Agent'

    def delivery_status(self, obj):
        status = obj.order.get_status_display()
        colors = {
            'out_for_delivery': 'orange',
            'delivered': 'green',
            'cancelled': 'red'
        }
        color = colors.get(obj.order.status, 'black')
        return format_html('<span style="color: {};">{}</span>', color, status)
    delivery_status.short_description = 'Order Status'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "agent" and 'order' in request.GET:
            try:
                order = Order.objects.get(id=request.GET['order'])
                kwargs["queryset"] = DeliveryAgent.objects.filter(
                    service_areas__code=order.pincode
                )
                if not kwargs["queryset"].exists():
                    self.message_user(request,
                                      "No agents available for this pincode!",
                                      messages.WARNING
                                      )
            except Order.DoesNotExist:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    class Media:
        css = {'all': ('css/admin/delivery_assignments.css',)}
