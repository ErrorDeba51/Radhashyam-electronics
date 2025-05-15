# radhashyam/products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from .models import (Product, ProductImage, ProductReview,
                     RelatedProduct, ProductCategory, Inventory, StockUpdate)

User = get_user_model()


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    classes = ['collapse']
    verbose_name = "Product Image"
    fields = ('image_preview', 'image', 'order')
    readonly_fields = ('image_preview',)
    ordering = ('order',)

    def image_preview(self, instance):
        if instance.image:
            return format_html('<img src="{}" height="50" />', instance.image.url)
        return "-"
    image_preview.short_description = 'Preview'


class InventoryInline(admin.StackedInline):
    model = Inventory
    fields = ('low_stock_threshold', 'is_auto_restock', 'stock_status')
    readonly_fields = ('stock_status',)
    extra = 0

    def stock_status(self, instance):
        return instance.get_stock_status_display()
    stock_status.short_description = 'Current Status'


class RelatedProductInline(admin.TabularInline):
    model = RelatedProduct
    fk_name = 'from_product'
    extra = 1
    autocomplete_fields = ['to_product']
    verbose_name = "Related Product"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'price',
        'stock_status',
        'average_rating',
        'review_count',
        'is_deal_of_week'
    )
    list_filter = ('category', 'is_deal_of_week')
    search_fields = ('title', 'description', 'category__name')
    inlines = [ProductImageInline, InventoryInline, RelatedProductInline]
    actions = ['toggle_deal_of_week', 'restock_products']
    list_per_page = 25
    list_editable = ('price', 'is_deal_of_week')
    readonly_fields = ('created_at', 'modified_at',
                       'average_rating', 'review_count')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'category')}),
        ('Pricing & Inventory', {'fields': ('price', 'stock')}),
        ('Promotions', {'fields': ('is_deal_of_week',)}),
        ('Details', {'fields': ('description', 'specs', 'warranty')}),
        ('Analytics', {'fields': ('average_rating', 'review_count')}),
        ('Metadata', {'fields': ('created_at', 'modified_at')}),
    )

    def stock_status(self, obj):
        return obj.inventory.get_stock_status_display()
    stock_status.short_description = 'Stock Status'

    def average_rating(self, obj):
        avg = obj.average_rating
        return format_html('<span style="color: {};">{}</span>',
                           '#f39c12' if avg else '#999',
                           f"{avg:.1f}★" if avg else "N/A")
    average_rating.admin_order_field = 'reviews__rating'

    def review_count(self, obj):
        return obj.review_count
    review_count.short_description = 'Reviews'

    def toggle_deal_of_week(self, request, queryset):
        for obj in queryset:
            obj.is_deal_of_week = not obj.is_deal_of_week
            obj.save()
    toggle_deal_of_week.short_description = "Toggle Deal of Week"

    def restock_products(self, request, queryset):
        updated = queryset.update(stock=models.F(
            'inventory__low_stock_threshold') + 10)
        self.message_user(request, f"Restocked {updated} products")
    restock_products.short_description = "Restock selected products"


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'featured', 'product_count', 'image_thumbnail')
    list_editable = ('featured',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'featured')}),
        ('Content', {'fields': ('description', 'image')}),
    )

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "-"
    image_thumbnail.short_description = 'Image Preview'

    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Products'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'is_approved',
                    'rating_stars', 'auto_approved', 'status', 'short_comment')
    list_filter = ('is_approved', 'rating', 'product')
    search_fields = ('comment', 'product__title', 'user__email')
    list_editable = ('is_approved',)
    actions = ['approve_reviews', 'auto_approve_eligible']
    raw_id_fields = ('product', 'user')
    readonly_fields = ('auto_approved',)

    fieldsets = (
        (None, {'fields': ('product', 'user')}),
        ('Review Content', {'fields': ('rating', 'comment')}),
        ('Moderation', {'fields': ('is_approved', 'auto_approved')}),
        ('Metadata', {'fields': ('created_at',)}),
    )

    def rating_stars(self, obj):
        return format_html(
            '<span style="color: {};">{}</span>',
            '#27ae60' if obj.is_approved else '#e74c3c',
            '★' * obj.rating + '☆' * (5 - obj.rating)
        )
    rating_stars.short_description = 'Rating'

    def auto_approved(self, obj):
        return obj.rating >= 4
    auto_approved.boolean = True
    auto_approved.short_description = 'Auto-Approved'

    def status(self, obj):
        if obj.is_approved:
            return format_html('<span style="color: #27ae60;">Approved</span>')
        return format_html('<span style="color: #e74c3c;">Pending</span>')
    status.short_description = 'Status'

    def short_comment(self, obj):
        return obj.comment[:75] + '...' if len(obj.comment) > 75 else obj.comment
    short_comment.short_description = 'Comment'

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"

    def auto_approve_eligible(self, request, queryset):
        eligible = queryset.filter(rating__gte=4).update(is_approved=True)
        self.message_user(request, f"Auto-approved {eligible} reviews")
    auto_approve_eligible.short_description = "Auto-approve eligible (4+ stars)"


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'stock_status',
                    'low_stock_threshold', 'last_restocked')
    list_filter = ()
    search_fields = ('product__title', 'sku')
    readonly_fields = ('stock_status', 'last_restocked')
    fields = ('product', 'sku', 'low_stock_threshold',
              'is_auto_restock', 'stock_status')


@admin.register(StockUpdate)
class StockUpdateAdmin(admin.ModelAdmin):
    list_display = ('product', 'old_stock', 'new_stock',
                    'changed_by', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('product__title', 'note')
    readonly_fields = ('timestamp',)
    fields = ('product', 'old_stock', 'new_stock', 'note', 'changed_by')
