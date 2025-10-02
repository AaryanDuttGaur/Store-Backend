from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from PIL import Image
import uuid


class Category(models.Model):
    """Product categories with hierarchical support"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Return full category path like: Electronics > Phones > Smartphones"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.append(parent.name)
            parent = parent.parent
        return " > ".join(reversed(path))


class Brand(models.Model):
    """Product brands/manufacturers"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    """Main product model with all professional e-commerce features"""
    
    # Basic Information
    name = models.CharField(max_length=200)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=100, unique=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags for search")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original price for showing discounts")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Cost for profit calculations")
    
    # Inventory
    track_quantity = models.BooleanField(default=True)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    allow_backorder = models.BooleanField(default=False)
    
    # Physical Properties
    weight = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True, help_text="Weight in kg")
    length = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Length in cm")
    width = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Width in cm")
    height = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Height in cm")
    
    # SEO and Marketing
    meta_title = models.CharField(max_length=60, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    featured = models.BooleanField(default=False, help_text="Show in featured products")
    
    # Status and Visibility
    is_active = models.BooleanField(default=True)
    is_digital = models.BooleanField(default=False)
    requires_shipping = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['featured', 'is_active']),
            models.Index(fields=['price']),
        ]

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"PRD-{uuid.uuid4().hex[:8].upper()}"
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.short_description and self.description:
            self.short_description = self.description[:255]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def is_on_sale(self):
        """Check if product is on sale"""
        return self.compare_price and self.compare_price > self.price

    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.is_on_sale:
            return round(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        if not self.track_quantity:
            return True
        return self.quantity > 0

    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        if not self.track_quantity:
            return False
        return self.quantity <= self.low_stock_threshold

    @property
    def main_image(self):
        """Get main product image"""
        main_img = self.images.filter(is_main=True).first()
        return main_img.image if main_img else None


class ProductImage(models.Model):
    """Product images with multiple image support"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_main = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'created_at']

    def save(self, *args, **kwargs):
        # Ensure only one main image per product
        if self.is_main:
            ProductImage.objects.filter(product=self.product, is_main=True).update(is_main=False)
        
        super().save(*args, **kwargs)
        
        # Resize image if too large
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800), Image.Resampling.LANCZOS)
                img.save(self.image.path)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    """Product variants (size, color, etc.)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100, help_text="e.g., 'Red - Large'")
    sku = models.CharField(max_length=100, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Leave blank to use product price")
    quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Variant attributes
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = f"{self.product.sku}-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def effective_price(self):
        """Return variant price or product price if variant price not set"""
        return self.price if self.price else self.product.price


class ProductReview(models.Model):
    """Customer product reviews"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    review = models.TextField()
    is_verified = models.BooleanField(default=False, help_text="Verified purchase")
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rating}★ - {self.title} by {self.customer_name}"


class ProductAttribute(models.Model):
    """Additional product attributes (specifications)"""
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=200)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'name']
        unique_together = ['product', 'name']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"