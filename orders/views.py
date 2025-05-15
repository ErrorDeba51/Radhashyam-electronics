# radhashyam/orders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.db import IntegrityError
from django.urls import reverse
from datetime import timedelta
import razorpay
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from decimal import Decimal
from django.views.decorators.http import require_http_methods
from products.models import Product, ProductReview
from cart.models import Cart
from .models import Order, OrderItem, Pincode, DeliveryAssignment, DeliveryAgent

pdfmetrics.registerFont(
    TTFont('NotoSans', 'static/fonts/NotoSans-Regular.ttf'))
pdfmetrics.registerFont(
    TTFont('NotoSans-Bold', 'static/fonts/NotoSans-Bold.ttf'))

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required
def create_order(request, product_id):
    """Create direct order for single product"""
    product = get_object_or_404(Product, id=product_id)
    order = Order.objects.create(
        user=request.user,
        product_total=product.price,
        total_amount=product.price,
        delivery_date=timezone.now() + timedelta(days=3),
        status='pending'
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1,
        price=product.price
    )
    return redirect('orders:checkout_with_order', order_id=order.id)


def generate_invoice(order):
    """Generate PDF invoice for order with professional layout"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    p = canvas.Canvas(response)

    try:
        p.drawImage("static/images/logo.png", 220, 750, width=150,
                    height=50, preserveAspectRatio=True)
    except:
        pass

    p.setFont("NotoSans-Bold", 14)
    p.drawCentredString(300, 730, "Radhashyam Electronics")
    p.setFont("NotoSans", 10)
    p.drawCentredString(
        300, 715, "Labpur, Thanapara, Birbhum - 731303, West Bengal")
    p.drawCentredString(300, 700, "Contact: 7001899476")

    p.line(50, 690, 550, 690)

    p.setFont("NotoSans-Bold", 12)
    p.drawString(50, 670, "Bill To:")
    p.setFont("NotoSans", 10)

    customer_details = [
        f"Name: {order.user.get_full_name()}",
        f"Address: {order.address}",
        f"Pincode: {order.pincode}",
        f"Phone: {order.phone}",
        f"Email: {order.user.email}"
    ]

    y_position = 650
    for line in customer_details:
        p.drawString(50, y_position, line)
        y_position -= 15

    p.setFont("NotoSans-Bold", 12)
    p.drawString(50, y_position-20, "Order Details:")
    p.setFont("NotoSans", 10)

    order_details = [
        f"Order ID: #ORD{order.id:06d}",
        f"Order Date: {order.created_at.strftime('%d-%b-%Y %H:%M')}",
        f"Expected Delivery: {order.delivery_date.strftime('%d-%b-%Y')}"
    ]

    y_position -= 40
    for line in order_details:
        p.drawString(50, y_position, line)
        y_position -= 15

    p.setFont("NotoSans-Bold", 10)
    y_position -= 30
    p.drawString(50, y_position, "Item Name")
    p.drawString(300, y_position, "Quantity")
    p.drawString(350, y_position, "Unit Price")
    p.drawString(420, y_position, "Warranty")
    p.drawString(500, y_position, "Total")
    p.line(50, y_position-2, 550, y_position-2)

    y_position -= 20
    p.setFont("NotoSans", 10)
    for item in order.items.all():
        product_name = item.product.title
        max_width = 200
        line_height = 12
        x_pos = 50

        lines = []
        current_line = []
        current_width = 0
        space_width = p.stringWidth(' ', "NotoSans", 10)

        for word in product_name.split():
            word_width = p.stringWidth(word, "NotoSans", 10)
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width + space_width
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width + space_width
        if current_line:
            lines.append(' '.join(current_line))

        for i, line in enumerate(lines):
            p.drawString(x_pos, y_position - (i * line_height), line)

        p.drawString(300, y_position, str(item.quantity))
        p.drawString(350, y_position, f"₹{item.price:.2f}")
        p.drawString(420, y_position, item.product.warranty)
        p.drawString(500, y_position, f"₹{item.total_price:.2f}")

        y_position -= (len(lines) * line_height) + \
            8

        if y_position < 100:
            p.showPage()
            y_position = 800
            p.setFont("NotoSans", 10)

    p.setFont("NotoSans-Bold", 12)
    y_position -= 30
    p.drawString(50, y_position, "Payment Summary:")
    y_position -= 20

    summary_data = [
        ("Product Total:", f"₹ {order.product_total:.2f}"),
        ("Delivery Charge:", f"₹ {order.delivery_charge:.2f}"),
    ]

    if order.payment_method == 'cod':
        summary_data.append(
            ("COD Advance Paid:", f"₹-{order.cod_advance_paid:.2f}"))

    summary_data.append(("Grand Total:", f"₹ {order.total_amount:.2f}"))
    summary_data.append(
        ("Payment Method:", order.get_payment_method_display().upper()))

    p.setFont("NotoSans", 10)
    for label, value in summary_data:
        p.drawString(100, y_position, label)
        p.drawString(400, y_position, value)
        y_position -= 20

    p.setFont("NotoSans", 8)
    footer_notes = [
        "Important Notes:",
        "1. We deliver only within Birbhum district.",
        "2. Contact our support team for installation assistance.",
        "3. Keep this invoice for warranty claims.",
        "4. Thank you for shopping with us!"
    ]

    y_position -= 40
    for note in footer_notes:
        p.drawString(50, y_position, note)
        y_position -= 12

    p.showPage()
    p.save()
    return response


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return generate_invoice(order)


@login_required
def checkout(request, order_id=None):
    """
    Handle both cart checkout and direct product checkout
    order_id=None: Cart checkout flow
    order_id=value: Direct product checkout flow
    """
    if order_id:
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if request.method == 'POST':
            return handle_checkout_post(request, order)

        valid_pincodes = Pincode.objects.filter(
            is_active=True)
        return render(request, 'orders/checkout.html', {
            'order': order,
            'valid_pincodes': valid_pincodes,
            'razorpay_key': settings.RAZORPAY_KEY_ID
        })

    if request.method == 'GET':
        selected_ids = request.GET.get('products', '').split(',')
        selected_ids = [int(id) for id in selected_ids if id.isdigit()]

        try:
            cart = Cart.objects.get(user=request.user)
            items = cart.items.filter(product__id__in=selected_ids)

            if not items.exists():
                return JsonResponse({
                    'error': 'No products selected for checkout',
                    'redirect': reverse('cart:cart_view')
                }, status=400)

            product_total = sum(item.total_price for item in items)
            order = Order.objects.create(
                user=request.user,
                product_total=product_total,
                total_amount=product_total,
                status='pending',
                delivery_date=timezone.now() + timedelta(days=7)
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )

            return redirect('orders:checkout_with_order', order_id=order.id)

        except Cart.DoesNotExist:
            return JsonResponse({
                'error': 'Cart not found',
                'redirect': reverse('cart:cart_view')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'redirect': reverse('home')
            }, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


def handle_checkout_post(request, order):
    """Handle POST request for checkout (shared by both flows)"""
    try:
        if not order.items.exists():
            return JsonResponse({
                'error': 'Order contains no items',
                'redirect': reverse('cart:cart_view')
            }, status=400)

        data = request.POST
        pincode = data.get('pincode', '').strip()
        payment_method = data.get('payment_method', '').strip()

        if not pincode or not payment_method:
            return JsonResponse({'error': 'All fields are required'}, status=400)

        pincode_data = Pincode.objects.get(code=pincode, is_active=True)

        order.pincode = pincode
        order.address = data.get('address', '')
        order.phone = data.get('phone', '')
        order.delivery_charge = Decimal(pincode_data.delivery_charge)
        order.total_amount = order.product_total + order.delivery_charge
        order.delivery_date = timezone.now() + timedelta(days=pincode_data.delivery_days)
        order.payment_method = payment_method

        if payment_method == 'cod':
            order.cod_advance_paid = Decimal(pincode_data.cod_advance)

        order.save()

        response_data = {
            'order_id': order.id,
            'delivery_charge': float(order.delivery_charge),
            'cod_advance': float(pincode_data.cod_advance),
            'total_amount': float(order.total_amount),
            'cod_available': payment_method == 'cod'
        }

        if payment_method == 'razorpay':
            payment_amount = int(order.total_amount * 100)
            payment_order = client.order.create({
                'amount': payment_amount,
                'currency': 'INR',
                'payment_capture': 1
            })
            response_data.update({
                'payment_required': True,
                'razorpay_order_id': payment_order['id'],
                'amount': payment_amount / 100
            })

        elif payment_method == 'cod':
            if pincode_data.cod_advance > 0:
                payment_amount = int(pincode_data.cod_advance * 100)
                payment_order = client.order.create({
                    'amount': payment_amount,
                    'currency': 'INR',
                    'payment_capture': 1
                })
                response_data.update({
                    'payment_required': True,
                    'razorpay_order_id': payment_order['id'],
                    'amount': payment_amount / 100,
                    'is_advance': True
                })
            else:
                response_data.update({
                    'payment_required': False,
                    'redirect_url': reverse('orders:order_tracking', kwargs={'order_id': order.id})
                })

        return JsonResponse(response_data)

    except Pincode.DoesNotExist:
        return JsonResponse({'error': 'Delivery not available for this pincode'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e), 'redirect': reverse('home')}, status=500)


@login_required
def payment_success(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)

    try:
        cart = Cart.objects.get(user=request.user)
        purchased_products = order.items.values_list('product', flat=True)
        cart.items.filter(product__in=purchased_products).delete()
        cart.save()
    except Cart.DoesNotExist:
        pass

    if order.payment_method == 'cod' and 'is_advance' in request.GET:
        try:
            pincode_data = Pincode.objects.get(
                code=order.pincode, is_active=True)
            order.cod_advance_paid = Decimal(pincode_data.cod_advance)
            order.status = 'confirmed'
            remaining = order.remaining_amount
            message = f'Advance payment successful! ₹{order.cod_advance_paid:.2f} paid. ₹{remaining:.2f} to be paid on delivery.'
        except Pincode.DoesNotExist:
            messages.error(request, 'Invalid pincode configuration')
            return redirect('orders:order_tracking', order_id=order.id)
    else:
        order.status = 'confirmed'
        message = 'Payment successful! Your order is being processed.'
        try:
            DeliveryAssignment.objects.get_or_create(
                order=order,
                defaults={'agent': DeliveryAgent.objects.filter(
                    service_areas__code=order.pincode,
                    is_available=True
                ).first()}
            )
        except Exception as e:
            messages.warning(request, 'Delivery agent assignment pending')

    order.save()
    messages.success(request, message)
    return redirect('orders:order_tracking', order_id=order.id)


@login_required
def payment_failure(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order.status = 'failed'
    order.save()
    messages.error(request, 'Payment failed. Please try again.')
    return redirect('orders:checkout')


@login_required
def order_tracking(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    delivery_assignment = getattr(order, 'delivery_assignment', None)

    status_sequence = [
        {'status': 'confirmed', 'label': 'Order Confirmed', 'icon': 'fa-check-circle'},
        {'status': 'processing', 'label': 'Processing', 'icon': 'fa-cog'},
        {'status': 'shipped', 'label': 'Shipped', 'icon': 'fa-shipping-fast'},
        {'status': 'out_for_delivery', 'label': 'Out for Delivery', 'icon': 'fa-truck'},
        {'status': 'delivered', 'label': 'Delivered', 'icon': 'fa-box-open'}
    ]

    return render(request, 'orders/tracking.html', {
        'order': order,
        'delivery_assignment': delivery_assignment,
        'status_sequence': status_sequence,
        'delivery_otp': order.delivery_otp if order.status == 'out_for_delivery' else None
    })


@login_required
def purchase_history(request):
    orders = Order.objects.filter(user=request.user).exclude(
        status='pending').order_by('-created_at')
    return render(request, 'orders/history.html', {'orders': orders})


@require_http_methods(["GET"])
def check_pincode(request):
    pincode = request.GET.get('pincode', '').strip()
    try:
        if len(pincode) != 6 or not pincode.isdigit():
            return JsonResponse({'valid': False, 'error': 'Invalid pincode format'})

        pincode_data = Pincode.objects.get(code=pincode, is_active=True)
        return JsonResponse({
            'valid': True,
            'cod_advance': float(pincode_data.cod_advance),
            'delivery_days': pincode_data.delivery_days,
            'delivery_charge': float(pincode_data.delivery_charge)
        })

    except Pincode.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Service unavailable for this pincode'})
    except Exception as e:
        return JsonResponse({'valid': False, 'error': str(e)}, status=400)


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', '')
        if cancellation_reason:
            order.status = 'cancelled'
            order.cancellation_reason = cancellation_reason
            order.save()
            messages.success(request, 'Order has been cancelled successfully')
            return redirect('orders:order_tracking', order_id=order.id)

    messages.error(request, 'Invalid cancellation request')
    return redirect('orders:order_tracking', order_id=order.id)


@login_required
def submit_feedback(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST' and order.status == 'delivered':
        rating = int(request.POST.get('rating', 0))
        comments = request.POST.get('comments', '')

        if 1 <= rating <= 5:
            for item in order.items.all():
                try:
                    ProductReview.objects.create(
                        product=item.product,
                        user=request.user,
                        rating=rating,
                        comment=comments
                    )
                except IntegrityError:
                    messages.error(
                        request, f"You've already reviewed {item.product.title}")
                    continue

            order.feedback_rating = rating
            order.feedback_comments = comments
            order.feedback_submitted_at = timezone.now()
            order.save()
            messages.success(request, 'Thank you for your feedback!')
        else:
            messages.error(request, 'Invalid rating submitted')

    return redirect('orders:order_tracking', order_id=order.id)
