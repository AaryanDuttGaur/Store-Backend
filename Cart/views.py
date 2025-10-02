from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Cart, CartItem
from .serializers import (
    CartSerializer, CartItemSerializer, AddToCartSerializer, 
    UpdateCartItemSerializer, CartSummarySerializer
)
from Product.models import Product, ProductVariant


class CartView(generics.RetrieveAPIView):
    """
    GET: Retrieve user's cart with all items
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Get or create cart for the authenticated user"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    def retrieve(self, request, *args, **kwargs):
        """Override to add extra cart info"""
        response = super().retrieve(request, *args, **kwargs)
        
        # Add additional cart summary
        cart = self.get_object()
        response.data['summary'] = {
            'has_items': cart.item_count > 0,
            'can_checkout': cart.item_count > 0 and cart.total_price > 0,
            'estimated_total': float(cart.total_price) if cart.total_price else 0.0
        }
        
        return response


class AddToCartView(generics.CreateAPIView):
    """
    POST: Add item to user's cart
    """
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Add item to cart with duplicate handling"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        product_id = serializer.validated_data['product_id']
        variant_id = serializer.validated_data.get('variant_id')
        quantity = serializer.validated_data['quantity']
        
        # Get or create user's cart
        cart, created = Cart.objects.get_or_create(user=user)
        
        # Get product and variant
        product = get_object_or_404(Product, id=product_id, is_active=True)
        variant = None
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, is_active=True)
        
        try:
            # Check if item already exists in cart
            cart_item = CartItem.objects.get(
                cart=cart,
                product=product,
                variant=variant
            )
            
            # Update quantity of existing item
            new_quantity = cart_item.quantity + quantity
            
            # Validate new quantity against stock
            available_stock = variant.quantity if variant else product.quantity
            if product.track_quantity and new_quantity > available_stock:
                return Response(
                    {'detail': f'Cannot add {quantity} more items. Only {available_stock - cart_item.quantity} more available.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = new_quantity
            cart_item.save()
            
            message = f"Updated quantity to {new_quantity}"
            
        except CartItem.DoesNotExist:
            # Create new cart item
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity
            )
            
            message = f"Added {quantity} item(s) to cart"
        
        # Return updated cart
        cart_serializer = CartSerializer(cart, context={'request': request})
        
        return Response({
            'message': message,
            'cart': cart_serializer.data,
            'item': CartItemSerializer(cart_item, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


class UpdateCartItemView(generics.UpdateAPIView):
    """
    PUT/PATCH: Update cart item quantity
    """
    serializer_class = UpdateCartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return cart items belonging to the authenticated user"""
        return CartItem.objects.filter(cart__user=self.request.user)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Update cart item quantity with stock validation"""
        cart_item = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_quantity = serializer.validated_data['quantity']
        
        # Validate against available stock
        if cart_item.product.track_quantity:
            available_stock = cart_item.variant.quantity if cart_item.variant else cart_item.product.quantity
            
            if new_quantity > available_stock:
                return Response(
                    {'detail': f'Only {available_stock} items available in stock.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Update quantity
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Return updated cart item
        return Response({
            'message': f'Updated quantity to {new_quantity}',
            'item': CartItemSerializer(cart_item, context={'request': request}).data,
            'cart_summary': CartSummarySerializer(cart_item.cart).data
        }, status=status.HTTP_200_OK)


class RemoveCartItemView(generics.DestroyAPIView):
    """
    DELETE: Remove item from cart
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Only return cart items belonging to the authenticated user"""
        return CartItem.objects.filter(cart__user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """Remove cart item and return updated cart summary"""
        cart_item = self.get_object()
        product_name = cart_item.product.name
        cart = cart_item.cart
        
        # Delete the cart item
        cart_item.delete()
        
        return Response({
            'message': f'Removed {product_name} from cart',
            'cart_summary': CartSummarySerializer(cart).data
        }, status=status.HTTP_200_OK)


class ClearCartView(generics.GenericAPIView):
    """
    DELETE: Clear all items from user's cart
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """Clear all items from cart"""
        try:
            cart = Cart.objects.get(user=request.user)
            items_count = cart.items.count()
            cart.items.all().delete()
            
            return Response({
                'message': f'Removed {items_count} items from cart',
                'cart_summary': CartSummarySerializer(cart).data
            }, status=status.HTTP_200_OK)
            
        except Cart.DoesNotExist:
            return Response({
                'message': 'Cart is already empty',
                'cart_summary': {
                    'id': None,
                    'total_items': 0,
                    'total_price': '0.00',
                    'item_count': 0
                }
            }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def cart_summary(request):
    """
    GET: Get lightweight cart summary for navbar
    """
    try:
        cart = Cart.objects.get(user=request.user)
        serializer = CartSummarySerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Cart.DoesNotExist:
        return Response({
            'id': None,
            'total_items': 0,
            'total_price': '0.00',
            'item_count': 0
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quick_add_to_cart(request, product_id):
    """
    POST: Quick add single item to cart (for product cards, shop page)
    """
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check stock
        if product.track_quantity and product.quantity <= 0:
            return Response(
                {'detail': 'Product is out of stock'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create cart
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        with transaction.atomic():
            # Check if item already exists
            try:
                cart_item = CartItem.objects.get(cart=cart, product=product, variant=None)
                
                # Check stock for additional quantity
                if product.track_quantity and cart_item.quantity >= product.quantity:
                    return Response(
                        {'detail': 'Cannot add more items. Maximum stock reached.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                cart_item.quantity += 1
                cart_item.save()
                message = f"Increased quantity to {cart_item.quantity}"
                
            except CartItem.DoesNotExist:
                # Create new cart item
                cart_item = CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=1
                )
                message = "Added to cart"
        
        return Response({
            'message': message,
            'cart_summary': CartSummarySerializer(cart).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'detail': f'Error adding to cart: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )