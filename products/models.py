# radhashyam/products/models.py
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.db.models import Avg


def product_image_upload_path(instance, filename):
    """Generate upload path for product images"""
    return f'products/{instance.product.id}/{filename}'


class ProductCategory(models.Model):
    """Product categories with SEO-friendly slugs"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    image = models.ImageField(upload_to='categories/%Y/%m/')
    featured = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Main product model with inventory tracking"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    warranty = models.CharField(max_length=100, blank=True)
    specs = models.TextField(
        help_text="Use bullet points (•) for specifications")
    is_deal_of_week = models.BooleanField(default=False)
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    related_products = models.ManyToManyField(
        'self',
        through='RelatedProduct',
        symmetrical=False,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=['is_deal_of_week']),
            models.Index(fields=['category', 'price']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def average_rating(self):
        return self.reviews.filter(is_approved=True).aggregate(Avg('rating'))['rating__avg']

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class RelatedProduct(models.Model):
    """Product relationship management"""
    from_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='related_from')
    to_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='related_to')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_product', 'to_product')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_product} → {self.to_product}"


class ProductImage(models.Model):
    """Product image storage with ordering support"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/%Y/%m/')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.title}"


class ProductReview(models.Model):
    """Customer reviews with auto-approval for high ratings"""
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        unique_together = ('product', 'user')
        ordering = ['-created_at']
        verbose_name = "Product Review"
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return f"{self.user}'s {self.rating}-star review of {self.product}"

    def save(self, *args, **kwargs):
        """Auto-approve high-rated reviews and update product rating"""
        if self.rating >= 4:
            self.is_approved = True

        super().save(*args, **kwargs)

        if self.is_approved:
            self.product.save()


class Inventory(models.Model):
    """Real-time inventory management system"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    low_stock_threshold = models.IntegerField(default=5)
    last_restocked = models.DateTimeField(auto_now_add=True)
    is_auto_restock = models.BooleanField(default=False)
    sku = models.CharField(max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name_plural = "Inventory"

    @property
    def stock_status(self):
        if self.product.stock <= 0:
            return 'out_of_stock'
        if self.product.stock <= self.low_stock_threshold:
            return 'low_stock'
        return 'in_stock'

    def __str__(self):
        return f"Inventory for {self.product}"


class StockUpdate(models.Model):
    """Historical stock change tracking"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    old_stock = models.IntegerField()
    new_stock = models.IntegerField()
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product} stock updated: {self.old_stock} → {self.new_stock}"
