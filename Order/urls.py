from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Order Management URLs
    path('create/', views.OrderCreateView.as_view(), name='order-create'),
    path('list/', views.OrderListView.as_view(), name='order-list'),
    path('detail/<str:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('update/<str:order_id>/', views.OrderUpdateView.as_view(), name='order-update'),
    path('cancel/<str:order_id>/', views.OrderCancelView.as_view(), name='order-cancel'),
    
    # Transaction Management URLs
    path('transactions/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transactions/<str:transaction_id>/', views.TransactionDetailView.as_view(), name='transaction-detail'),
    
    # Order Statistics and Analytics
    path('stats/', views.order_stats, name='order-stats'),
    path('admin/stats/', views.admin_order_stats, name='admin-order-stats'),
    path('analytics/delivery/', views.delivery_analytics, name='delivery-analytics'),
    
    # Order Actions
    path('reorder/<str:order_id>/', views.reorder, name='reorder'),
    path('invoice/<str:order_id>/', views.order_invoice, name='order-invoice'),
    path('refund/<str:order_id>/', views.refund_order, name='refund-order'),
]