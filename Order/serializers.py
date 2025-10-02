from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.db import models
from decimal import Decimal
from datetime import datetime, timedelta
from .models import Order, OrderItem, Transaction, OrderStatusHistory, DeliveryEvent
from Product.models import Product, ProductVariant


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField()
    product_sku = serializers.ReadOnlyField()
    product_image = serializers.SerializerMethodField()
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'variant', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price', 'product_image']
        read_only_fields = ['product_name', 'product_sku', 'total_price']
    
    def get_product_image(self, obj):
        try:
            main_image = obj.product.images.filter(is_main=True).first()
            if main_image and main_image.image:
                request = self.context.get('request')
                return request.build_absolute_uri(main_image.image.url) if request else main_image.image.url
        except:
            pass
        return None


class OrderItemCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = OrderItem
        fields = ['product_id', 'variant_id', 'quantity', 'unit_price']
        extra_kwargs = {'unit_price': {'required': False}}
    
    def validate_product_id(self, value):
        try:
            Product.objects.get(id=value, is_active=True)
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
    
    def validate_variant_id(self, value):
        if value:
            try:
                ProductVariant.objects.get(id=value, is_active=True)
                return value
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found or inactive")
        return value
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value


class TransactionSerializer(serializers.ModelSerializer):
    masked_payment_info = serializers.ReadOnlyField()
    is_successful = serializers.ReadOnlyField()
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'transaction_id', 'transaction_type', 'payment_method', 'payment_method_display', 
                 'amount', 'currency', 'status', 'status_display', 'gateway', 'masked_payment_info', 
                 'is_successful', 'created_at', 'processed_at', 'failure_reason']
        read_only_fields = ['transaction_id', 'gateway', 'gateway_transaction_id', 'created_at', 'processed_at']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = ['id', 'status', 'status_display', 'notes', 'changed_by', 'changed_by_name', 'created_at']
        read_only_fields = ['created_at']


class DeliveryEventSerializer(serializers.ModelSerializer):
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    
    class Meta:
        model = DeliveryEvent
        fields = ['id', 'event_type', 'event_type_display', 'event_date', 'location', 'description', 'carrier_reference', 'created_at']
        read_only_fields = ['created_at']


class OrderListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    shipping_method_display = serializers.ReadOnlyField()
    delivery_status_display = serializers.ReadOnlyField()
    is_delivery_overdue = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'status', 'status_display', 'payment_status', 'payment_status_display', 
                 'total_amount', 'total_items', 'item_count', 'created_at', 'estimated_delivery_date', 
                 'tracking_number', 'shipping_method', 'shipping_method_display', 'delivery_status_display',
                 'is_delivery_overdue', 'shipping_duration', 'is_free_shipping']


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    transaction = TransactionSerializer(read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    delivery_events = DeliveryEventSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    shipping_method_display = serializers.ReadOnlyField()
    delivery_status_display = serializers.ReadOnlyField()
    is_delivery_overdue = serializers.ReadOnlyField()
    total_items = serializers.ReadOnlyField()
    item_count = serializers.ReadOnlyField()
    full_shipping_address = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = ['id', 'order_id', 'status', 'status_display', 'payment_status', 'payment_status_display', 
                 'created_at', 'updated_at', 'customer_email', 'customer_phone', 'shipping_first_name', 
                 'shipping_last_name', 'shipping_address_line_1', 'shipping_address_line_2', 'shipping_city',
                 'shipping_state', 'shipping_postal_code', 'shipping_country', 'full_shipping_address',
                 'billing_same_as_shipping', 'billing_first_name', 'billing_last_name', 'billing_address_line_1',
                 'billing_address_line_2', 'billing_city', 'billing_state', 'billing_postal_code', 'billing_country',
                 'subtotal', 'shipping_cost', 'tax_amount', 'total_amount', 'total_items', 'item_count',
                 'shipping_method', 'shipping_method_display', 'shipping_duration', 'estimated_delivery_date',
                 'delivery_instructions', 'is_free_shipping', 'shipping_carrier', 'tracking_number', 'shipped_at',
                 'delivered_at', 'notes', 'delivery_status_display', 'is_delivery_overdue', 'out_for_delivery_at',
                 'delivery_attempted_at', 'delivery_confirmation_method', 'items', 'transaction', 'status_history', 'delivery_events']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)
    customer_info = serializers.DictField(write_only=True, required=False)
    payment_info = serializers.DictField(write_only=True, required=False)
    shipping_method = serializers.CharField(write_only=True, required=False)
    shipping_method_type = serializers.CharField(write_only=True, required=False)
    shipping_cost = serializers.DecimalField(max_digits=8, decimal_places=2, write_only=True, required=False)
    estimated_delivery = serializers.CharField(write_only=True, required=False)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    tax_amount = serializers.DecimalField(max_digits=8, decimal_places=2, write_only=True, required=False)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    
    class Meta:
        model = Order
        fields = ['customer_email', 'customer_phone', 'shipping_first_name', 'shipping_last_name', 
                 'shipping_address_line_1', 'shipping_address_line_2', 'shipping_city', 'shipping_state',
                 'shipping_postal_code', 'shipping_country', 'billing_same_as_shipping', 'billing_first_name', 
                 'billing_last_name', 'billing_address_line_1', 'billing_address_line_2', 'billing_city',
                 'billing_state', 'billing_postal_code', 'billing_country', 'estimated_delivery_date',
                 'delivery_instructions', 'shipping_carrier', 'notes', 'items', 'customer_info', 'payment_info', 
                 'shipping_method', 'shipping_method_type', 'shipping_cost', 'estimated_delivery',
                 'subtotal', 'tax_amount', 'total_amount']
        extra_kwargs = {
            'customer_email': {'required': True},
            'shipping_first_name': {'required': True},
            'shipping_last_name': {'required': True},
            'shipping_address_line_1': {'required': True},
            'shipping_city': {'required': True},
            'shipping_state': {'required': True},
            'shipping_postal_code': {'required': True},
        }
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        
        for item_data in value:
            try:
                product = Product.objects.get(id=item_data['product_id'], is_active=True)
                if product.track_quantity and item_data['quantity'] > product.quantity:
                    raise serializers.ValidationError(f"Insufficient stock for {product.name}. Available: {product.quantity}")
            except Product.DoesNotExist:
                raise serializers.ValidationError(f"Product with ID {item_data['product_id']} not found")
        return value
    
    def validate_customer_info(self, value):
        if value and 'email' in value and not value['email'].strip():
            raise serializers.ValidationError("Email is required in customer_info")
        return value
    
    def validate_payment_info(self, value):
        if value:
            required_fields = ['card_number', 'expiry', 'cvv']
            for field in required_fields:
                if field not in value or not str(value[field]).strip():
                    raise serializers.ValidationError(f"{field} is required in payment_info")
        return value
    
    def _normalize_shipping_method(self, shipping_method_input):
        """Normalize shipping method to match model choices"""
        if not shipping_method_input:
            return 'standard'
            
        # Handle both display names and codes
        method_mapping = {
            'Standard Shipping': 'standard',
            'Express Shipping': 'express', 
            'Overnight Shipping': 'overnight',
            'standard': 'standard',
            'express': 'express',
            'overnight': 'overnight',
        }
        return method_mapping.get(shipping_method_input, 'standard')
    
    def _calculate_estimated_delivery_date(self, shipping_method):
        """Calculate estimated delivery date based on shipping method"""
        base_date = timezone.now().date()
        delivery_days = {
            'standard': 7, 
            'express': 3, 
            'overnight': 1
        }
        days_to_add = delivery_days.get(shipping_method, 7)
        return base_date + timedelta(days=days_to_add)
    
    def _get_shipping_cost(self, method, subtotal):
        """Calculate shipping cost based on method and subtotal"""
        shipping_costs = {
            'standard': Decimal('0.00'), 
            'express': Decimal('15.99'), 
            'overnight': Decimal('29.99')
        }
        cost = shipping_costs.get(method, Decimal('0.00'))
        # Free standard shipping over $50
        return Decimal('0.00') if method == 'standard' and subtotal >= 50 else cost
    
    def _parse_estimated_delivery_string(self, estimated_delivery_str):
        """Parse estimated delivery string from frontend"""
        if not estimated_delivery_str:
            return None
        try:
            current_year = datetime.now().year
            clean_date = estimated_delivery_str.strip()
            
            # Remove weekday if present
            if ',' in clean_date:
                clean_date = clean_date.split(',', 1)[1].strip()
            
            # Try different date formats
            for fmt in ['%b %d', '%B %d', '%m/%d', '%m-%d']:
                try:
                    parsed_date = datetime.strptime(clean_date, fmt).replace(year=current_year)
                    return parsed_date.date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    @transaction.atomic
    def create(self, validated_data):
        # Extract nested data
        items_data = validated_data.pop('items')
        customer_info = validated_data.pop('customer_info', {})
        payment_info = validated_data.pop('payment_info', {})
        
        # Get shipping method
        shipping_method_input = (
            validated_data.pop('shipping_method', None) or 
            validated_data.pop('shipping_method_type', None) or 
            'standard'
        )
        
        # Get frontend values
        frontend_shipping_cost = validated_data.pop('shipping_cost', None)
        frontend_subtotal = validated_data.pop('subtotal', None)
        frontend_tax = validated_data.pop('tax_amount', None)
        frontend_total = validated_data.pop('total_amount', None)
        estimated_delivery_str = validated_data.pop('estimated_delivery', '')
        
        # Set user
        user = self.context['request'].user
        validated_data['user'] = user
        
        # Process customer info
        if customer_info:
            if not validated_data.get('customer_email'):
                validated_data['customer_email'] = customer_info.get('email', user.email)
            
            # Parse full name
            full_name = customer_info.get('full_name', '')
            if full_name and not validated_data.get('shipping_first_name'):
                name_parts = full_name.strip().split()
                validated_data['shipping_first_name'] = name_parts[0] if name_parts else ''
                validated_data['shipping_last_name'] = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
            
            # Other customer info
            if customer_info.get('delivery_instructions'):
                validated_data['delivery_instructions'] = customer_info['delivery_instructions']
            
            if customer_info.get('phone') and not validated_data.get('customer_phone'):
                validated_data['customer_phone'] = customer_info['phone']
        
        # Normalize shipping method
        shipping_method_code = self._normalize_shipping_method(shipping_method_input)
        
        # Calculate or use provided subtotal
        if frontend_subtotal:
            subtotal = Decimal(str(frontend_subtotal))
        else:
            subtotal = Decimal('0.00')
            for item_data in items_data:
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                    variant = None
                    if item_data.get('variant_id'):
                        variant = ProductVariant.objects.get(id=item_data['variant_id'])
                    
                    unit_price = item_data.get('unit_price')
                    if not unit_price:
                        unit_price = variant.effective_price if variant else product.price
                    
                    quantity = item_data['quantity']
                    subtotal += Decimal(str(unit_price)) * quantity
                    
                except (Product.DoesNotExist, ProductVariant.DoesNotExist):
                    raise serializers.ValidationError("Invalid product or variant")
        
        # Set shipping method details
        validated_data['shipping_method'] = shipping_method_code
        
        method_display_names = {
            'standard': 'Standard Shipping',
            'express': 'Express Shipping',
            'overnight': 'Overnight Shipping',
        }
        validated_data['shipping_method_display'] = method_display_names.get(shipping_method_code, 'Standard Shipping')
        
        # Calculate shipping cost
        if frontend_shipping_cost is not None:
            shipping_cost = Decimal(str(frontend_shipping_cost))
        else:
            shipping_cost = self._get_shipping_cost(shipping_method_code, subtotal)
        
        # Calculate tax
        if frontend_tax is not None:
            tax_amount = Decimal(str(frontend_tax))
        else:
            tax_amount = subtotal * Decimal('0.08')  # 8% tax
        
        # Calculate total
        if frontend_total is not None:
            total_amount = Decimal(str(frontend_total))
        else:
            total_amount = subtotal + shipping_cost + tax_amount
        
        # Update validated_data with calculated values
        validated_data.update({
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'is_free_shipping': (shipping_cost == 0 and subtotal >= 50)
        })
        
        # Set estimated delivery date
        parsed_delivery_date = self._parse_estimated_delivery_string(estimated_delivery_str)
        if parsed_delivery_date:
            validated_data['estimated_delivery_date'] = parsed_delivery_date
        else:
            validated_data['estimated_delivery_date'] = self._calculate_estimated_delivery_date(shipping_method_code)
        
        # Set shipping duration
        duration_map = {
            'standard': '5-7 business days', 
            'express': '2-3 business days', 
            'overnight': '1 business day'
        }
        validated_data['shipping_duration'] = duration_map.get(shipping_method_code, '5-7 business days')
        
        # Set default values
        if not validated_data.get('shipping_carrier'):
            validated_data['shipping_carrier'] = 'Standard Carrier'
        
        if not validated_data.get('shipping_country'):
            validated_data['shipping_country'] = 'United States'
        
        # Create the order
        order = super().create(validated_data)
        
        # Create order items
        for item_data in items_data:
            try:
                product = Product.objects.get(id=item_data['product_id'])
                variant = None
                if item_data.get('variant_id'):
                    variant = ProductVariant.objects.get(id=item_data['variant_id'])
                
                unit_price = item_data.get('unit_price')
                if not unit_price:
                    unit_price = variant.effective_price if variant else product.price
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    quantity=item_data['quantity'],
                    unit_price=unit_price,
                    product_name=product.name,
                    product_sku=variant.sku if variant else product.sku
                )
                
                # Update product stock
                if product.track_quantity:
                    product.quantity -= item_data['quantity']
                    product.save()
                    
            except (Product.DoesNotExist, ProductVariant.DoesNotExist) as e:
                raise serializers.ValidationError(f"Error creating order item: {str(e)}")
        
        # Create transaction if payment info provided
        if payment_info:
            try:
                Transaction.objects.create(
                    order=order,
                    transaction_type='payment',
                    payment_method='credit_card',
                    amount=order.total_amount,
                    status='completed',
                    payment_details={
                        'last_four': str(payment_info.get('card_number', ''))[-4:] if payment_info.get('card_number') else '****',
                        'expiry': payment_info.get('expiry', ''),
                    },
                    gateway_response={
                        'status': 'success', 
                        'message': 'Payment processed successfully'
                    }
                )
                
                order.payment_status = 'completed'
                order.save()
            except Exception as e:
                raise serializers.ValidationError(f"Error creating transaction: {str(e)}")
        
        # Create status history
        try:
            OrderStatusHistory.objects.create(
                order=order,
                status='pending',
                notes=f'Order created via checkout with {order.shipping_method_display}',
                changed_by=user
            )
        except Exception as e:
            # Log the error but don't fail the order creation
            pass
        
        # Create initial delivery event
        try:
            DeliveryEvent.objects.create(
                order=order,
                event_type='picked_up',
                event_date=order.created_at,
                description=f'Order placed for {order.shipping_method_display}. Expected delivery: {order.estimated_delivery_date}',
                location='Processing Center',
                carrier_reference=f'REF-{order.order_id}'
            )
        except Exception as e:
            # Log the error but don't fail the order creation
            pass
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    status_note = serializers.CharField(write_only=True, required=False, allow_blank=True)
    delivery_event_type = serializers.CharField(write_only=True, required=False)
    delivery_event_location = serializers.CharField(write_only=True, required=False)
    delivery_event_description = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'tracking_number', 'estimated_delivery_date', 'notes', 'status_note',
                 'shipping_carrier', 'delivery_instructions', 'delivery_confirmation_method', 'out_for_delivery_at',
                 'delivery_attempted_at', 'delivered_at', 'delivery_event_type', 'delivery_event_location', 'delivery_event_description']
    
    def update(self, instance, validated_data):
        status_note = validated_data.pop('status_note', '')
        delivery_event_type = validated_data.pop('delivery_event_type', '')
        delivery_event_location = validated_data.pop('delivery_event_location', '')
        delivery_event_description = validated_data.pop('delivery_event_description', '')
        
        old_status = instance.status
        order = super().update(instance, validated_data)
        
        # Create status history if status changed
        if 'status' in validated_data and validated_data['status'] != old_status:
            try:
                OrderStatusHistory.objects.create(
                    order=order,
                    status=validated_data['status'],
                    notes=status_note or f'Status changed from {old_status} to {validated_data["status"]}',
                    changed_by=self.context['request'].user if self.context.get('request') else None
                )
            except Exception as e:
                pass  # Log error but don't fail update
        
        # Create delivery event if provided
        if delivery_event_type:
            try:
                DeliveryEvent.objects.create(
                    order=order,
                    event_type=delivery_event_type,
                    event_date=timezone.now(),
                    location=delivery_event_location,
                    description=delivery_event_description or f'Order {delivery_event_type.replace("_", " ").title()}'
                )
            except Exception as e:
                pass  # Log error but don't fail update
        
        return order


class TransactionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['order', 'transaction_type', 'payment_method', 'amount', 'currency', 'gateway', 'payment_details', 'failure_reason']
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def validate(self, data):
        transaction_type = data.get('transaction_type')
        order = data.get('order')
        
        if transaction_type in ['refund', 'partial_refund'] and order:
            if data['amount'] > order.total_amount:
                raise serializers.ValidationError("Refund amount cannot exceed order total")
        return data


class DeliveryEventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryEvent
        fields = ['order', 'event_type', 'event_date', 'location', 'description', 'carrier_reference']
        extra_kwargs = {'event_date': {'required': False}}
    
    def create(self, validated_data):
        if 'event_date' not in validated_data:
            validated_data['event_date'] = timezone.now()
        return super().create(validated_data)