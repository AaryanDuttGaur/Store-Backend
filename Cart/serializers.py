from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Cart, CartItem
from Product.models import Product, ProductVariant
from Product.serializers import ProductListSerializer, ProductVariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for individual cart items with product details"""
    
    # Include product details
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    
    # Calculated fields
    subtotal = serializers.ReadOnlyField()
    current_price = serializers.ReadOnlyField()
    price_changed = serializers.ReadOnlyField()
    
    # For creating/updating cart items
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'price_when_added',
            'subtotal', 'current_price', 'price_changed', 'added_at', 'updated_at',
            # Write-only fields for creating items
            'product_id', 'variant_id'
        ]
        read_only_fields = ['id', 'price_when_added', 'added_at', 'updated_at']
    
    def validate_product_id(self, value):
        """Validate that product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or not available.")
    
    def validate_variant_id(self, value):
        """Validate that variant exists if provided"""
        if value is not None:
            try:
                variant = ProductVariant.objects.get(id=value, is_active=True)
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found or not available.")
        return value
    
    def validate_quantity(self, value):
        """Validate quantity is positive and reasonable"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        if value > 99:
            raise serializers.ValidationError("Maximum quantity allowed is 99.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)
        
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                
                # Check stock if product tracks quantity
                if product.track_quantity:
                    available_stock = product.quantity
                    
                    # If variant selected, check variant stock
                    if variant_id:
                        variant = ProductVariant.objects.get(id=variant_id)
                        available_stock = variant.quantity
                    
                    if quantity > available_stock:
                        raise serializers.ValidationError(
                            f"Only {available_stock} items available in stock."
                        )
                
                # Validate variant belongs to product
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id)
                    if variant.product_id != product_id:
                        raise serializers.ValidationError(
                            "Selected variant does not belong to this product."
                        )
                        
            except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                raise serializers.ValidationError("Invalid product or variant.")
        
        return data


class CartSerializer(serializers.ModelSerializer):
    """Complete cart serializer with all items and totals"""
    
    # Include all cart items
    items = CartItemSerializer(many=True, read_only=True)
    
    # Calculated totals
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    
    # User info (optional)
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id', 'user_info', 'items', 'total_items', 'total_price', 
            'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """Get basic user info for cart"""
        if obj.user:
            return {
                'username': obj.user.username,
                'customer_id': getattr(obj.user.profile, 'customer_id', None)
            }
        return {'username': 'Guest', 'customer_id': None}


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(default=1)
    
    def validate_product_id(self, value):
        """Validate product exists and is active"""
        try:
            product = Product.objects.get(id=value, is_active=True)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or not available.")
    
    def validate_variant_id(self, value):
        """Validate variant exists if provided"""
        if value is not None:
            try:
                variant = ProductVariant.objects.get(id=value, is_active=True)
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found or not available.")
        return value
    
    def validate_quantity(self, value):
        """Validate quantity"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        if value > 99:
            raise serializers.ValidationError("Maximum quantity allowed is 99.")
        return value
    
    def validate(self, data):
        """Cross-field validation - same as CartItemSerializer"""
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)
        
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                
                # Check stock
                if product.track_quantity:
                    available_stock = product.quantity
                    
                    if variant_id:
                        variant = ProductVariant.objects.get(id=variant_id)
                        available_stock = variant.quantity
                    
                    if quantity > available_stock:
                        raise serializers.ValidationError(
                            f"Only {available_stock} items available in stock."
                        )
                
                # Validate variant belongs to product
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id)
                    if variant.product_id != product_id:
                        raise serializers.ValidationError(
                            "Selected variant does not belong to this product."
                        )
                        
            except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                raise serializers.ValidationError("Invalid product or variant.")
        
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    
    quantity = serializers.IntegerField()
    
    def validate_quantity(self, value):
        """Validate quantity"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        if value > 99:
            raise serializers.ValidationError("Maximum quantity allowed is 99.")
        return value


class CartSummarySerializer(serializers.ModelSerializer):
    """Lightweight cart summary for navbar/quick view"""
    
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Cart
        fields = ['id', 'total_items', 'total_price', 'item_count']