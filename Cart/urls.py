from django.urls import path
from .views import (
    CartView, AddToCartView, UpdateCartItemView, RemoveCartItemView,
    ClearCartView, cart_summary, quick_add_to_cart
)

urlpatterns = [
    # Main cart endpoints
    path('', CartView.as_view(), name='cart-detail'),  # GET: Get full cart
    path('add/', AddToCartView.as_view(), name='add-to-cart'),  # POST: Add item to cart
    path('clear/', ClearCartView.as_view(), name='clear-cart'),  # DELETE: Clear entire cart
    
    # Cart item management
    path('items/<int:pk>/', UpdateCartItemView.as_view(), name='update-cart-item'),  # PUT: Update item quantity
    path('items/<int:pk>/remove/', RemoveCartItemView.as_view(), name='remove-cart-item'),  # DELETE: Remove specific item
    
    # Quick actions
    path('summary/', cart_summary, name='cart-summary'),  # GET: Lightweight cart summary for navbar
    path('quick-add/<int:product_id>/', quick_add_to_cart, name='quick-add-to-cart'),  # POST: One-click add to cart
]