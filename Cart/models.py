from django.db import models
from django.contrib.auth.models import User
from Product.models import Product, ProductVariant
from django.core.validators import MinValueValidator
import uuid


class Cart(models.Model):
    """
    Cart model - One cart per user
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='cart',
        help_text="User who owns this cart"
    )
    
    # For guest users (optional - can be used later)
    session_key = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Session key for guest users"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Shopping Cart"
        verbose_name_plural = "Shopping Carts"
    
    def __str__(self):
        return f"Cart for {self.user.username if self.user else f'Guest-{self.session_key}'}"
    
    @property
    def total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        """Calculate total price of all items in cart"""
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def item_count(self):
        """Get count of different products in cart (not quantity)"""
        return self.items.count()


class CartItem(models.Model):
    """
    Individual items in a cart
    """
    cart = models.ForeignKey(
        Cart, 
        on_delete=models.CASCADE, 
        related_name='items',
        help_text="Cart this item belongs to"
    )
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        help_text="Product being added to cart"
    )
    
    # Optional: if product has variants (size, color, etc.)
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        help_text="Product variant (size, color, etc.)"
    )
    
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Quantity of this product in cart"
    )
    
    # Store price at the time of adding to cart (for price change protection)
    price_when_added = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Product price when added to cart"
    )
    
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"
        # Prevent duplicate items (same product + variant in same cart)
        unique_together = ['cart', 'product', 'variant']
    
    def save(self, *args, **kwargs):
        """Auto-set price when adding item to cart"""
        if not self.price_when_added:
            if self.variant:
                self.price_when_added = self.variant.effective_price
            else:
                self.price_when_added = self.product.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.quantity}x {self.product.name}{variant_info} in {self.cart.user.username}'s cart"
    
    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        return self.quantity * self.price_when_added
    
    @property
    def current_price(self):
        """Get current product price (may be different from price_when_added)"""
        if self.variant:
            return self.variant.effective_price
        return self.product.price
    
    @property
    def price_changed(self):
        """Check if product price changed since adding to cart"""
        return self.price_when_added != self.current_price