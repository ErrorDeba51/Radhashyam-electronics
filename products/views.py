# radhashyam/products/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q, Avg, Exists, OuterRef
from django.template.loader import render_to_string
from django_filters import rest_framework as filters
from orders.models import OrderItem
from .models import Product, ProductCategory, ProductReview
from django.db import IntegrityError


def home(request):
    """Display home page with featured products and deals"""
    deals = Product.objects.filter(
        is_deal_of_week=True).prefetch_related('images')[:8]
    categories = ProductCategory.objects.all()
    products = Product.objects.order_by('?').prefetch_related('images')

    return render(request, 'products/home.html', {
        'deals': deals,
        'categories': categories,
        'products': products
    })


def appliance_view(request):
    """Display appliance categories overview"""
    categories = ProductCategory.objects.all()
    return render(request, 'products/appliance.html', {'categories': categories})


def product_detail(request, pk):
    product = get_object_or_404(
        Product.objects.annotate(
            avg_rating=Avg('reviews__rating', filter=Q(
                reviews__is_approved=True))
        ).prefetch_related('images', 'reviews'),
        id=pk
    )

    related_products = Product.objects.filter(
        category=product.category
    ).exclude(id=product.id).prefetch_related('images')[:8]

    user_can_review = False
    if request.user.is_authenticated:
        user_can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__status='delivered',
            product=product
        ).exists()

    return render(request, 'products/detail.html', {
        'product': product,
        'related_products': related_products,
        'user_can_review': user_can_review
    })


def category_view(request, slug):
    """Display products in a specific category"""
    category = get_object_or_404(ProductCategory, slug=slug)
    products = Product.objects.filter(
        category=category).prefetch_related('images')
    return render(request, 'products/category.html', {
        'category': category,
        'products': products
    })


def product_search(request):
    """Handle AJAX product search requests"""
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(category__name__icontains=query)
    )[:20]

    results = [{
        'title': p.title,
        'price': float(p.price),
        'image': p.images.first().image.url if p.images.exists() else '',
        'url': reverse('products:product_detail', args=[p.id]),
        'rating': p.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg'] or 0
    } for p in products]

    return JsonResponse({'results': results})


class ProductFilter(filters.FilterSet):
    min_price = filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = filters.NumberFilter(field_name="price", lookup_expr='lte')
    q = filters.CharFilter(method='custom_search')

    class Meta:
        model = Product
        fields = []

    def custom_search(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(category__name__icontains=value)
        ).distinct()


def advanced_search(request):
    queryset = Product.objects.all().prefetch_related('images')
    product_filter = ProductFilter(request.GET, queryset=queryset)

    if request.headers.get('HX-Request'):
        return render(request, 'products/partials/product_grid.html', {
            'filter': product_filter,
            'products': product_filter.qs,
            'request': request
        })

    return render(request, 'products/search.html', {
        'filter': product_filter,
        'products': product_filter.qs,
        'request': request
    })


def submit_review(request, product_id):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        product = get_object_or_404(Product, id=product_id)
        rating = int(request.POST.get('rating', 0))
        comment = request.POST.get('comment', '')

        if not (1 <= rating <= 5):
            return JsonResponse({'success': False, 'error': 'Invalid rating'})

        try:
            review = ProductReview.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                comment=comment
            )
        except IntegrityError:
            return JsonResponse({'success': False, 'error': 'You have already reviewed this product.'})

        product = Product.objects.annotate(
            average_rating=Avg('reviews__rating', filter=Q(
                reviews__is_approved=True))
        ).prefetch_related('reviews').get(id=product_id)

        approved_reviews = product.reviews.filter(is_approved=True)
        review_html = ''

        if review.is_approved:
            review_html = render_to_string(
                'products/partials/review_item.html', {'review': review})

        return JsonResponse({
            'success': True,
            'review_html': review_html,
            'new_rating': render_to_string('products/partials/rating_stars.html', {'product': product}),
            'review_count': approved_reviews.count(),
            'average_rating': f"{product.average_rating:.1f}" if product.average_rating else '0.0'
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})
