from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count, Avg, F
from django.db import transaction as db_transaction
from django.utils import timezone
from django.contrib.auth.models import User
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Order, OrderItem, Transaction, OrderStatusHistory, DeliveryEvent
from .serializers import (
    OrderCreateSerializer, OrderDetailSerializer, OrderListSerializer,
    OrderUpdateSerializer, TransactionSerializer, TransactionCreateSerializer,
    OrderStatusHistorySerializer, DeliveryEventSerializer, DeliveryEventCreateSerializer
)
from Product.models import Product, ProductVariant
from UserAuth.models import CustomerProfile


class OrderPagination(PageNumberPagination):
    """Custom pagination for orders"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class OrderCreateView(generics.CreateAPIView):
    """
    POST: Create a new order during checkout with enhanced delivery tracking
    Handles the complete checkout process including:
    - Order creation with delivery information
    - Order items
    - Transaction processing
    - Stock management
    - Status history
    - Initial delivery event creation
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Enhanced order creation with detailed response including delivery tracking"""
        try:
            with db_transaction.atomic():
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                order = serializer.save()
                
                # Return detailed order information with delivery tracking
                order_serializer = OrderDetailSerializer(order, context={'request': request})
                
                # Create initial delivery tracking events
                delivery_errors = self._create_initial_delivery_events(order, request.user)
                if delivery_errors:
                    raise Exception(delivery_errors)
                
                return Response({
                    'success': True,
                    'message': f'Order {order.order_id} created successfully!',
                    'order': order_serializer.data,
                    'order_id': order.order_id,
                    'total_amount': float(order.total_amount),
                    'estimated_delivery_date': order.estimated_delivery_date,
                    'estimated_delivery_formatted': order.estimated_delivery_date.strftime('%A, %B %d, %Y') if order.estimated_delivery_date else None,
                    'shipping_method': order.shipping_method_display,
                    'shipping_duration': order.shipping_duration,
                    'tracking_info': {
                        'can_track': bool(order.tracking_number),
                        'tracking_number': order.tracking_number,
                        'carrier': order.shipping_carrier,
                        'estimated_delivery': order.estimated_delivery_date
                    }
                }, status=status.HTTP_201_CREATED)
                
        except serializers.ValidationError as e:
            return Response({
                'success': False,
                'message': 'Failed to create order',
                'error': e.detail  # Detailed validation errors from serializer
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to create order',
                'error': str(e) if not hasattr(e, 'detail') else e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_initial_delivery_events(self, order, user):
        """Create initial delivery tracking events"""
        try:
            # Order placed event
            DeliveryEvent.objects.create(
                order=order,
                event_type='picked_up',
                event_date=order.created_at,
                location='Processing Center',
                description=f'Order {order.order_id} has been placed and is being prepared for shipment.',
                carrier_reference=f'REF-{order.order_id}'
            )
            
            # If express or overnight, add additional tracking precision
            if order.shipping_method in ['express', 'overnight']:
                DeliveryEvent.objects.create(
                    order=order,
                    event_type='in_transit',
                    event_date=order.created_at + timedelta(hours=2),
                    location='Shipping Facility',
                    description=f'Priority shipment for {order.shipping_method_display} has been processed.',
                    carrier_reference=f'PRIORITY-{order.order_id}'
                )
            return None
        except Exception as e:
            return f"Failed to create initial delivery events: {str(e)}"


class OrderDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a specific order
    """
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        """Filter orders by current user"""
        return Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items', 'delivery_events')

    def retrieve(self, request, *args, **kwargs):
        """Handle GET request for order details"""
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={'request': request})
        return Response({
            'success': True,
            'order': serializer.data,
            'tracking_info': {
                'can_track': bool(instance.tracking_number),
                'tracking_number': instance.tracking_number,
                'carrier': instance.shipping_carrier,
                'estimated_delivery': instance.estimated_delivery_date
            }
        })


class OrderUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH: Update order details (admin/staff only)
    """
    serializer_class = OrderUpdateSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'
    
    def get_queryset(self):
        """Get all orders for admin users"""
        return Order.objects.all().select_related('user').prefetch_related('items', 'delivery_events')
    
    def update(self, request, *args, **kwargs):
        """Handle order update with enhanced response"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        order = serializer.save()
        
        # Return updated order details
        order_serializer = OrderDetailSerializer(order, context={'request': request})
        
        return Response({
            'success': True,
            'message': f'Order {order.order_id} updated successfully',
            'order': order_serializer.data
        })


class OrderCancelView(generics.UpdateAPIView):
    """
    POST: Cancel an order (customer can cancel pending/confirmed orders)
    """
    serializer_class = OrderUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'
    
    def get_queryset(self):
        """Filter orders by current user"""
        return Order.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """Cancel the order"""
        instance = self.get_object()
        
        # Check if order can be cancelled
        if instance.status not in ['pending', 'confirmed']:
            return Response({
                'success': False,
                'message': f'Order {instance.order_id} cannot be cancelled. Current status: {instance.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cancel the order
        instance.status = 'cancelled'
        instance.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=instance,
            status='cancelled',
            notes='Order cancelled by customer',
            changed_by=request.user
        )
        
        # Create delivery event
        DeliveryEvent.objects.create(
            order=instance,
            event_type='returned',
            event_date=timezone.now(),
            location='Customer Request',
            description=f'Order {instance.order_id} cancelled by customer'
        )
        
        return Response({
            'success': True,
            'message': f'Order {instance.order_id} has been cancelled successfully'
        })


class OrderListView(generics.ListAPIView):
    """
    GET: List user's orders with enhanced filtering and delivery status
    Supports query parameters:
    - status: filter by order status
    - payment_status: filter by payment status  
    - date_from, date_to: filter by date range
    - delivery_status: filter by delivery status
    - shipping_method: filter by shipping method
    - search: search in order_id, product names
    """
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filter fields
    filterset_fields = ['status', 'payment_status', 'shipping_method']
    
    # Search fields
    search_fields = ['order_id', 'items__product_name', 'customer_email', 'tracking_number']
    
    # Ordering fields
    ordering_fields = ['created_at', 'total_amount', 'status', 'estimated_delivery_date']
    ordering = ['-created_at']  # Default ordering
    
    def get_queryset(self):
        """Filter orders by current user with optimizations and enhanced filtering"""
        queryset = Order.objects.filter(user=self.request.user).select_related('user').prefetch_related('items', 'delivery_events')
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Amount range filtering
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        
        if min_amount:
            try:
                queryset = queryset.filter(total_amount__gte=Decimal(min_amount))
            except:
                pass
        
        if max_amount:
            try:
                queryset = queryset.filter(total_amount__lte=Decimal(max_amount))
            except:
                pass
        
        # Delivery status filtering
        delivery_status = self.request.query_params.get('delivery_status')
        if delivery_status:
            if delivery_status == 'overdue':
                queryset = queryset.filter(
                    estimated_delivery_date__lt=timezone.now().date(),
                    status__in=['pending', 'confirmed', 'processing', 'shipped']
                )
            elif delivery_status == 'on_time':
                queryset = queryset.filter(
                    estimated_delivery_date__gte=timezone.now().date(),
                    status__in=['pending', 'confirmed', 'processing', 'shipped']
                )
            elif delivery_status == 'delivered':
                queryset = queryset.filter(status='delivered')
        
        # Free shipping filter
        free_shipping = self.request.query_params.get('free_shipping')
        if free_shipping == 'true':
            queryset = queryset.filter(is_free_shipping=True)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Enhanced list response with delivery statistics"""
        response = super().list(request, *args, **kwargs)
        
        # Get base queryset for statistics
        base_queryset = self.get_queryset()
        
        orders_stats = base_queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount'),
            pending_orders=Count('id', filter=Q(status='pending')),
            processing_orders=Count('id', filter=Q(status='processing')),
            shipped_orders=Count('id', filter=Q(status='shipped')),
            delivered_orders=Count('id', filter=Q(status='delivered')),
            cancelled_orders=Count('id', filter=Q(status='cancelled'))
        )
        
        delivery_stats = base_queryset.aggregate(
            overdue_orders=Count('id', filter=Q(
                estimated_delivery_date__lt=timezone.now().date(),
                status__in=['pending', 'confirmed', 'processing', 'shipped']
            )),
            on_time_deliveries=Count('id', filter=Q(
                status='delivered',
                delivered_at__date__lte=F('estimated_delivery_date')
            )),
            late_deliveries=Count('id', filter=Q(
                status='delivered',
                delivered_at__date__gt=F('estimated_delivery_date')
            )),
            total_shipping_revenue=Sum('shipping_cost'),
            free_shipping_orders=Count('id', filter=Q(is_free_shipping=True)),
            express_orders=Count('id', filter=Q(shipping_method='express')),
            standard_orders=Count('id', filter=Q(shipping_method='standard')),
            overnight_orders=Count('id', filter=Q(shipping_method='overnight'))
        )
        
        # Add statistics to response
        response.data.update({
            'overall_stats': {
                'total_orders': orders_stats['total_orders'] or 0,
                'total_revenue': float(orders_stats['total_revenue'] or 0),
                'average_order_value': float(orders_stats['avg_order_value'] or 0),
                'pending_orders': orders_stats['pending_orders'] or 0,
                'processing_orders': orders_stats['processing_orders'] or 0,
                'shipped_orders': orders_stats['shipped_orders'] or 0,
                'delivered_orders': orders_stats['delivered_orders'] or 0,
                'cancelled_orders': orders_stats['cancelled_orders'] or 0
            },
            'delivery_performance': {
                'overdue_orders': delivery_stats['overdue_orders'] or 0,
                'on_time_deliveries': delivery_stats['on_time_deliveries'] or 0,
                'late_deliveries': delivery_stats['late_deliveries'] or 0,
                'delivery_success_rate': round(
                    (delivery_stats['on_time_deliveries'] / max(orders_stats['delivered_orders'], 1)) * 100, 1
                ) if orders_stats['delivered_orders'] else 0,
                'total_shipping_revenue': float(delivery_stats['total_shipping_revenue'] or 0),
                'free_shipping_orders': delivery_stats['free_shipping_orders'] or 0,
                'express_orders': delivery_stats['express_orders'] or 0,
                'standard_orders': delivery_stats['standard_orders'] or 0,
                'overnight_orders': delivery_stats['overnight_orders'] or 0
            }
        })
        
        return response


class TransactionListView(generics.ListAPIView):
    """
    GET: List user's transactions
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Filter transactions by current user's orders"""
        return Transaction.objects.filter(order__user=self.request.user).select_related('order').order_by('-created_at')


class TransactionDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve details of a specific transaction
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'transaction_id'
    lookup_url_kwarg = 'transaction_id'
    
    def get_queryset(self):
        """Filter transactions by current user's orders"""
        return Transaction.objects.filter(order__user=self.request.user).select_related('order')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_stats(request):
    """
    GET: Get order statistics for current user
    """
    user_orders = Order.objects.filter(user=request.user)
    
    stats = user_orders.aggregate(
        total_orders=Count('id'),
        total_spent=Sum('total_amount'),
        avg_order_value=Avg('total_amount'),
        pending_orders=Count('id', filter=Q(status='pending')),
        delivered_orders=Count('id', filter=Q(status='delivered')),
        cancelled_orders=Count('id', filter=Q(status='cancelled'))
    )
    
    # Recent orders
    recent_orders = user_orders.order_by('-created_at')[:5].values(
        'order_id', 'status', 'total_amount', 'created_at'
    )
    
    return Response({
        'success': True,
        'stats': {
            'total_orders': stats['total_orders'] or 0,
            'total_spent': float(stats['total_spent'] or 0),
            'average_order_value': float(stats['avg_order_value'] or 0),
            'pending_orders': stats['pending_orders'] or 0,
            'delivered_orders': stats['delivered_orders'] or 0,
            'cancelled_orders': stats['cancelled_orders'] or 0,
        },
        'recent_orders': list(recent_orders)
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def admin_order_stats(request):
    """
    GET: Get comprehensive order statistics for admin dashboard
    """
    # Overall statistics
    all_orders = Order.objects.all()
    
    overall_stats = all_orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_amount'),
        avg_order_value=Avg('total_amount'),
        pending_orders=Count('id', filter=Q(status='pending')),
        processing_orders=Count('id', filter=Q(status='processing')),
        shipped_orders=Count('id', filter=Q(status='shipped')),
        delivered_orders=Count('id', filter=Q(status='delivered')),
        cancelled_orders=Count('id', filter=Q(status='cancelled'))
    )
    
    # Today's statistics
    today = timezone.now().date()
    today_orders = all_orders.filter(created_at__date=today)
    
    today_stats = today_orders.aggregate(
        orders_today=Count('id'),
        revenue_today=Sum('total_amount')
    )
    
    # Monthly statistics (last 12 months)
    monthly_data = []
    for i in range(12):
        month_start = (timezone.now() - timedelta(days=30*i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_stats = all_orders.filter(
            created_at__date__range=[month_start, month_end]
        ).aggregate(
            orders=Count('id'),
            revenue=Sum('total_amount')
        )
        
        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'orders': month_stats['orders'] or 0,
            'revenue': float(month_stats['revenue'] or 0)
        })
    
    return Response({
        'success': True,
        'overall_stats': {
            'total_orders': overall_stats['total_orders'] or 0,
            'total_revenue': float(overall_stats['total_revenue'] or 0),
            'average_order_value': float(overall_stats['avg_order_value'] or 0),
            'pending_orders': overall_stats['pending_orders'] or 0,
            'processing_orders': overall_stats['processing_orders'] or 0,
            'shipped_orders': overall_stats['shipped_orders'] or 0,
            'delivered_orders': overall_stats['delivered_orders'] or 0,
            'cancelled_orders': overall_stats['cancelled_orders'] or 0
        },
        'today_stats': {
            'orders_today': today_stats['orders_today'] or 0,
            'revenue_today': float(today_stats['revenue_today'] or 0)
        },
        'monthly_data': list(reversed(monthly_data))
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reorder(request, order_id):
    """
    POST: Reorder items from a previous order
    """
    try:
        # Get the original order
        original_order = get_object_or_404(Order, order_id=order_id, user=request.user)
        
        # Check if all items are still available
        unavailable_items = []
        for item in original_order.items.all():
            if not item.product.is_active:
                unavailable_items.append(item.product_name)
            elif item.product.track_quantity and item.quantity > item.product.quantity:
                unavailable_items.append(f"{item.product_name} (insufficient stock)")
        
        if unavailable_items:
            return Response({
                'success': False,
                'message': 'Some items are no longer available',
                'unavailable_items': unavailable_items
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order data for reorder
        order_data = {
            'items': [
                {
                    'product_id': item.product.id,
                    'quantity': item.quantity,
                    'unit_price': float(item.product.price)  # Use current price
                }
                for item in original_order.items.all()
            ],
            'customer_email': original_order.customer_email,
            'customer_phone': original_order.customer_phone,
            'shipping_first_name': original_order.shipping_first_name,
            'shipping_last_name': original_order.shipping_last_name,
            'shipping_address_line_1': original_order.shipping_address_line_1,
            'shipping_address_line_2': original_order.shipping_address_line_2,
            'shipping_city': original_order.shipping_city,
            'shipping_state': original_order.shipping_state,
            'shipping_postal_code': original_order.shipping_postal_code,
            'shipping_country': original_order.shipping_country,
            'shipping_method': original_order.shipping_method,
            'notes': f'Reorder of {original_order.order_id}'
        }
        
        # Create new order
        serializer = OrderCreateSerializer(data=order_data, context={'request': request})
        if serializer.is_valid():
            new_order = serializer.save()
            
            return Response({
                'success': True,
                'message': f'Reorder completed! New order: {new_order.order_id}',
                'new_order_id': new_order.order_id
            })
        else:
            return Response({
                'success': False,
                'message': 'Failed to create reorder',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Original order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Reorder failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_invoice(request, order_id):
    """
    GET: Get order invoice data
    """
    try:
        order = get_object_or_404(Order, order_id=order_id, user=request.user)
        order_data = OrderDetailSerializer(order, context={'request': request}).data
        
        return Response({
            'success': True,
            'invoice': {
                'order': order_data,
                'generated_at': timezone.now(),
                'invoice_number': f'INV-{order.order_id}'
            }
        })
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def refund_order(request, order_id):
    """
    POST: Process order refund (admin only)
    """
    try:
        order = get_object_or_404(Order, order_id=order_id)
        
        if order.status not in ['delivered', 'shipped']:
            return Response({
                'success': False,
                'message': 'Order cannot be refunded in current status'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create refund transaction
        refund_amount = request.data.get('amount', order.total_amount)
        reason = request.data.get('reason', 'Customer refund request')
        
        Transaction.objects.create(
            order=order,
            transaction_type='refund',
            payment_method=order.transaction.payment_method if hasattr(order, 'transaction') else 'credit_card',
            amount=refund_amount,
            status='completed',
            gateway_response={
                'status': 'success',
                'message': f'Refund processed: {reason}'
            }
        )
        
        # Update order status
        order.status = 'refunded'
        order.payment_status = 'refunded'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='refunded',
            notes=f'Refund processed: ${refund_amount}. Reason: {reason}',
            changed_by=request.user
        )
        
        return Response({
            'success': True,
            'message': f'Refund of ${refund_amount} processed successfully for order {order_id}'
        })
        
    except Order.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Order not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Refund failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def delivery_analytics(request):
    """
    GET: Get detailed delivery analytics for operations dashboard
    """
    # Time-based delivery performance
    time_ranges = {
        'last_7_days': 7,
        'last_30_days': 30,
        'last_90_days': 90
    }
    
    analytics = {}
    
    for period, days in time_ranges.items():
        start_date = timezone.now().date() - timedelta(days=days)
        period_orders = Order.objects.filter(created_at__date__gte=start_date)
        
        analytics[period] = {
            'total_orders': period_orders.count(),
            'delivered_orders': period_orders.filter(status='delivered').count(),
            'on_time_deliveries': period_orders.filter(
                status='delivered',
                delivered_at__date__lte=F('estimated_delivery_date')
            ).count(),
            'overdue_orders': period_orders.filter(
                estimated_delivery_date__lt=timezone.now().date(),
                status__in=['pending', 'confirmed', 'processing', 'shipped']
            ).count(),
            'avg_delivery_time': period_orders.filter(status='delivered').aggregate(
                avg_time=Avg(F('delivered_at') - F('created_at'))
            )['avg_time']
        }
        
        # Convert timedelta to days
        if analytics[period]['avg_delivery_time']:
            analytics[period]['avg_delivery_time'] = analytics[period]['avg_delivery_time'].days
    
    # Carrier performance (mock data for demo)
    carrier_performance = [
        {
            'carrier': 'Standard Carrier',
            'total_shipments': Order.objects.filter(shipping_carrier='Standard Carrier').count(),
            'on_time_rate': 94.5,
            'avg_delivery_days': 5.2,
            'cost_efficiency': 'High'
        },
        {
            'carrier': 'Express Carrier',
            'total_shipments': Order.objects.filter(shipping_method='express').count(),
            'on_time_rate': 97.8,
            'avg_delivery_days': 2.1,
            'cost_efficiency': 'Medium'
        },
        {
            'carrier': 'Overnight Carrier',
            'total_shipments': Order.objects.filter(shipping_method='overnight').count(),
            'on_time_rate': 99.2,
            'avg_delivery_days': 1.0,
            'cost_efficiency': 'Low'
        }
    ]
    
    # Geographic delivery insights
    geographic_stats = Order.objects.values('shipping_state').annotate(
        order_count=Count('id'),
        avg_delivery_time=Avg(
            F('delivered_at') - F('created_at'),
            filter=Q(status='delivered')
        ),
        on_time_rate=Count('id', filter=Q(
            status='delivered',
            delivered_at__date__lte=F('estimated_delivery_date')
        )) * 100.0 / Count('id', filter=Q(status='delivered'))
    ).order_by('-order_count')[:10]
    
    return Response({
        'time_based_performance': analytics,
        'carrier_performance': carrier_performance,
        'geographic_insights': [
            {
                'state': stat['shipping_state'],
                'order_count': stat['order_count'],
                'avg_delivery_days': stat['avg_delivery_time'].days if stat['avg_delivery_time'] else 0,
                'on_time_percentage': round(stat['on_time_rate'] or 0, 1)
            }
            for stat in geographic_stats
        ]
    })