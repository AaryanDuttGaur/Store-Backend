from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from Product.models import Product, ProductVariant
import uuid
from decimal import Decimal


class Order(models.Model):
    """
    Main order model containing all order information
    """
    # Order status choices
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Shipping method choices to match frontend options
    SHIPPING_METHOD_CHOICES = [
        ('standard', 'Standard Shipping'),
        ('express', 'Express Shipping'),
        ('overnight', 'Overnight Shipping'),
    ]
    
    # Order identification
    order_id = models.CharField(
        max_length=20, 
        unique=True, 
        blank=True,
        help_text="Unique order identifier (e.g., ORD-12345678)"
    )
    
    # Customer information
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='orders',
        help_text="Customer who placed the order"
    )
    
    # Customer details at time of order (for record keeping)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Shipping information
    shipping_first_name = models.CharField(max_length=50)
    shipping_last_name = models.CharField(max_length=50)
    shipping_address_line_1 = models.CharField(max_length=200)
    shipping_address_line_2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default='United States')
    
    # Billing information (optional - can use shipping if same)
    billing_same_as_shipping = models.BooleanField(default=True)
    billing_first_name = models.CharField(max_length=50, blank=True)
    billing_last_name = models.CharField(max_length=50, blank=True)
    billing_address_line_1 = models.CharField(max_length=200, blank=True)
    billing_address_line_2 = models.CharField(max_length=200, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    # Order totals
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total before shipping and tax"
    )
    shipping_cost = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=Decimal('0.00'),
        validators=[MinValueValidator(0)]
    )
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Final total amount"
    )
    
    # Order status
    status = models.CharField(
        max_length=20, 
        choices=ORDER_STATUS_CHOICES, 
        default='pending'
    )
    payment_status = models.CharField(
        max_length=20, 
        choices=PAYMENT_STATUS_CHOICES, 
        default='pending'
    )
    
    # Additional order information
    notes = models.TextField(
        blank=True,
        help_text="Special instructions or notes from customer"
    )
    
    # Enhanced Shipping and Delivery Details
    shipping_method = models.CharField(
        max_length=20,
        choices=SHIPPING_METHOD_CHOICES,
        default='standard',
        help_text="Selected shipping method type"
    )
    
    shipping_method_display = models.CharField(
        max_length=100, 
        default='Standard Shipping',
        help_text="Display name for shipping method"
    )
    
    shipping_duration = models.CharField(
        max_length=50,
        blank=True,
        help_text="Expected shipping duration (e.g., '5-7 business days')"
    )
    
    estimated_delivery_date = models.DateField(
        null=True, 
        blank=True,
        help_text="Estimated delivery date calculated at checkout"
    )
    
    delivery_instructions = models.TextField(
        blank=True,
        help_text="Special delivery instructions from customer"
    )
    
    is_free_shipping = models.BooleanField(
        default=False,
        help_text="Whether this order qualified for free shipping"
    )
    
    shipping_carrier = models.CharField(
        max_length=100,
        blank=True,
        default='Standard Carrier',
        help_text="Shipping carrier/company"
    )
    
    # Existing tracking and delivery fields
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # New delivery tracking fields
    out_for_delivery_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When order went out for delivery"
    )
    
    delivery_attempted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When delivery was first attempted"
    )
    
    delivery_confirmation_method = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('signature', 'Signature Required'),
            ('photo', 'Photo Confirmation'),
            ('contactless', 'Contactless Delivery'),
            ('mailbox', 'Mailbox Delivery'),
            ('front_door', 'Front Door'),
            ('other', 'Other'),
        ],
        help_text="How delivery was confirmed"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['shipping_method']),
            models.Index(fields=['estimated_delivery_date']),
        ]
    
    def save(self, *args, **kwargs):
        """Generate order ID if not provided"""
        if not self.order_id:
            self.order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Set shipping duration based on method if not provided
        if not self.shipping_duration and self.shipping_method:
            duration_map = {
                'standard': '5-7 business days',
                'express': '2-3 business days',
                'overnight': '1 business day',
            }
            self.shipping_duration = duration_map.get(self.shipping_method, '5-7 business days')
        
        # Set is_free_shipping flag
        if self.shipping_cost == 0 and self.subtotal >= 50:
            self.is_free_shipping = True
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_id} - {self.user.username}"
    
    @property
    def full_shipping_address(self):
        """Get formatted shipping address"""
        address_parts = [
            f"{self.shipping_first_name} {self.shipping_last_name}",
            self.shipping_address_line_1,
        ]
        if self.shipping_address_line_2:
            address_parts.append(self.shipping_address_line_2)
        address_parts.extend([
            f"{self.shipping_city}, {self.shipping_state} {self.shipping_postal_code}",
            self.shipping_country
        ])
        return "\n".join(address_parts)
    
    @property
    def total_items(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def item_count(self):
        """Get count of different products in order"""
        return self.items.count()
    
    @property
    def delivery_status_display(self):
        """Get user-friendly delivery status"""
        if self.status == 'delivered':
            return f"Delivered on {self.delivered_at.strftime('%B %d, %Y') if self.delivered_at else 'Unknown date'}"
        elif self.status == 'shipped':
            if self.out_for_delivery_at:
                return "Out for delivery"
            return f"Shipped - Expected: {self.estimated_delivery_date.strftime('%B %d, %Y') if self.estimated_delivery_date else 'TBD'}"
        elif self.status in ['processing', 'confirmed']:
            return f"Being prepared - Expected: {self.estimated_delivery_date.strftime('%B %d, %Y') if self.estimated_delivery_date else 'TBD'}"
        else:
            return self.get_status_display()
    
    @property
    def is_delivery_overdue(self):
        """Check if delivery is overdue"""
        from django.utils import timezone
        if self.estimated_delivery_date and self.status not in ['delivered', 'cancelled', 'refunded']:
            return timezone.now().date() > self.estimated_delivery_date
        return False


class OrderItem(models.Model):
    """
    Individual items within an order
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        help_text="Order this item belongs to"
    )
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        help_text="Product being ordered"
    )
    
    # Product variant if applicable
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Product variant (size, color, etc.)"
    )
    
    # Item details at time of order
    product_name = models.CharField(
        max_length=200,
        help_text="Product name at time of order"
    )
    product_sku = models.CharField(
        max_length=100,
        help_text="Product SKU at time of order"
    )
    
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Quantity ordered"
    )
    
    # Price snapshot (important for order history)
    unit_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price per unit at time of order"
    )
    
    total_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Total price for this item (unit_price * quantity)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
    
    def save(self, *args, **kwargs):
        """Auto-calculate total price and set product details"""
        # Set product details at time of order
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_sku:
            self.product_sku = self.product.sku
        
        # Set unit price from product or variant
        if not self.unit_price:
            if self.variant:
                self.unit_price = self.variant.effective_price
            else:
                self.unit_price = self.product.price
        
        # Calculate total price
        self.total_price = self.unit_price * self.quantity
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        variant_info = f" ({self.variant.name})" if self.variant else ""
        return f"{self.quantity}x {self.product_name}{variant_info} - {self.order.order_id}"


class Transaction(models.Model):
    """
    Transaction/Payment record for orders
    """
    TRANSACTION_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('partial_refund', 'Partial Refund'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    # Transaction identification
    transaction_id = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,
        help_text="Unique transaction identifier"
    )
    
    # Related order
    order = models.OneToOneField(
        Order, 
        on_delete=models.CASCADE, 
        related_name='transaction',
        help_text="Order this transaction belongs to"
    )
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPE_CHOICES, 
        default='payment'
    )
    
    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES,
        help_text="Payment method used"
    )
    
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Transaction amount"
    )
    
    currency = models.CharField(max_length=3, default='USD')
    
    status = models.CharField(
        max_length=20, 
        choices=TRANSACTION_STATUS_CHOICES, 
        default='pending'
    )
    
    # Payment gateway details (for demo purposes, we'll use mock data)
    gateway = models.CharField(
        max_length=50, 
        default='Mock Payment Gateway',
        help_text="Payment processor used"
    )
    gateway_transaction_id = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Transaction ID from payment gateway"
    )
    
    # Payment details (masked for security)
    payment_details = models.JSONField(
        default=dict,
        help_text="Payment method details (masked for security)"
    )
    
    # Transaction response from gateway
    gateway_response = models.JSONField(
        default=dict,
        help_text="Response data from payment gateway"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Failure information
    failure_reason = models.TextField(
        blank=True,
        help_text="Reason for transaction failure"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def save(self, *args, **kwargs):
        """Generate transaction ID if not provided"""
        if not self.transaction_id:
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        
        # Set gateway transaction ID for demo
        if not self.gateway_transaction_id:
            self.gateway_transaction_id = f"MOCK-{uuid.uuid4().hex[:16].upper()}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.order.order_id} - ${self.amount}"
    
    @property
    def is_successful(self):
        """Check if transaction is successful"""
        return self.status == 'completed'
    
    @property
    def masked_payment_info(self):
        """Get masked payment information for display"""
        if self.payment_method in ['credit_card', 'debit_card']:
            card_last_four = self.payment_details.get('last_four', '****')
            return f"**** **** **** {card_last_four}"
        elif self.payment_method == 'paypal':
            email = self.payment_details.get('email', 'user@example.com')
            return f"PayPal - {email}"
        else:
            return self.get_payment_method_display()


class OrderStatusHistory(models.Model):
    """
    Track order status changes for transparency
    """
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='status_history'
    )
    
    status = models.CharField(max_length=20, choices=Order.ORDER_STATUS_CHOICES)
    notes = models.TextField(blank=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        return f"{self.order.order_id} - {self.status} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


# New model for tracking delivery events
class DeliveryEvent(models.Model):
    """
    Track delivery events and updates for better customer communication
    """
    EVENT_TYPE_CHOICES = [
        ('picked_up', 'Picked Up from Warehouse'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivery_attempted', 'Delivery Attempted'),
        ('delivered', 'Delivered'),
        ('exception', 'Delivery Exception'),
        ('returned', 'Returned to Sender'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='delivery_events'
    )
    
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES
    )
    
    event_date = models.DateTimeField(
        help_text="When this delivery event occurred"
    )
    
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Location where event occurred"
    )
    
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the event"
    )
    
    carrier_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Carrier's reference for this event"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-event_date']
        verbose_name = "Delivery Event"
        verbose_name_plural = "Delivery Events"
    
    def __str__(self):
        return f"{self.order.order_id} - {self.get_event_type_display()} - {self.event_date}"