from django.urls import path
from .views import (
    ProductListView, ProductDetailView, FeaturedProductsView,
    CategoryListView, BrandListView, ProductReviewListCreateView,
    search_suggestions, product_filters, homepage_data
)

urlpatterns = [
    # Product endpoints
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:id>/', ProductDetailView.as_view(), name='product-detail'),
    path('products/featured/', FeaturedProductsView.as_view(), name='featured-products'),
    
    # Category endpoints
    path('categories/', CategoryListView.as_view(), name='category-list'),
    
    # Brand endpoints
    path('brands/', BrandListView.as_view(), name='brand-list'),
    
    # Review endpoints
    path('products/<int:product_id>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
    
    # Search and filter endpoints
    path('search/suggestions/', search_suggestions, name='search-suggestions'),
    path('filters/', product_filters, name='product-filters'),
    
    # Homepage data endpoint
    path('homepage/', homepage_data, name='homepage-data'),
]