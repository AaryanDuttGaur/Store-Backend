from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Min, Max  # Added Min, Max imports
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, Brand, ProductReview, ProductVariant  # Added missing imports
from .serializers import (
    ProductListSerializer, ProductDetailSerializer, CategorySerializer,
    BrandSerializer, ProductReviewSerializer
)


class ProductPagination(PageNumberPagination):
    """Custom pagination for products"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductListView(generics.ListAPIView):
    """
    GET: List all products with filtering, searching, and pagination
    Supports query parameters:
    - search: search in name, description, tags
    - category: filter by category ID
    - brand: filter by brand ID
    - min_price, max_price: price range filtering
    - featured: filter featured products
    - in_stock: filter products in stock
    - ordering: sort by price, name, created_at, rating
    """
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Search fields
    search_fields = ['name', 'description', 'tags', 'short_description']
    
    # Ordering fields
    ordering_fields = ['price', 'name', 'created_at', 'updated_at']
    ordering = ['-created_at']  # Default ordering
    
    # Filter fields
    filterset_fields = ['category', 'brand', 'featured', 'is_active']
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related('images')
        
        # Custom filters
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        in_stock = self.request.query_params.get('in_stock')
        rating_min = self.request.query_params.get('rating_min')
        
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        if in_stock and in_stock.lower() == 'true':
            queryset = queryset.filter(
                Q(track_quantity=False) | Q(quantity__gt=0)
            )
        
        if rating_min:
            try:
                # Filter products with minimum average rating
                queryset = queryset.annotate(
                    avg_rating=Avg('reviews__rating')
                ).filter(avg_rating__gte=float(rating_min))
            except ValueError:
                pass
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override to add extra data in response"""
        response = super().list(request, *args, **kwargs)
        
        # Add filter options to response
        response.data['filters'] = {
            'categories': CategorySerializer(Category.objects.filter(is_active=True), many=True).data,
            'brands': BrandSerializer(Brand.objects.filter(is_active=True), many=True).data,
            'price_range': {
                'min': Product.objects.filter(is_active=True).aggregate(min_price=Min('price'))['min_price'] or 0,
                'max': Product.objects.filter(is_active=True).aggregate(max_price=Max('price'))['max_price'] or 0,
            }
        }
        
        return response


class ProductDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve detailed product information including:
    - Full product details
    - All images
    - Variants
    - Attributes
    - Reviews with pagination
    - Related products
    """
    serializer_class = ProductDetailSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).select_related('category', 'brand').prefetch_related(
            'images', 'variants', 'attributes', 'reviews'
        )
    
    def retrieve(self, request, *args, **kwargs):
        """Override to add related products and review summary"""
        response = super().retrieve(request, *args, **kwargs)
        product = self.get_object()
        
        # Add related products (same category, excluding current)
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        response.data['related_products'] = ProductListSerializer(related_products, many=True).data
        
        # Add review summary
        reviews = product.reviews.filter(is_approved=True)
        if reviews.exists():
            response.data['review_summary'] = {
                'total_reviews': reviews.count(),
                'average_rating': reviews.aggregate(avg=Avg('rating'))['avg'],
                'rating_distribution': {
                    '5': reviews.filter(rating=5).count(),
                    '4': reviews.filter(rating=4).count(),
                    '3': reviews.filter(rating=3).count(),
                    '2': reviews.filter(rating=2).count(),
                    '1': reviews.filter(rating=1).count(),
                }
            }
        else:
            response.data['review_summary'] = {
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {'5': 0, '4': 0, '3': 0, '2': 0, '1': 0}
            }
        
        return response


class FeaturedProductsView(generics.ListAPIView):
    """GET: List featured products for homepage"""
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True, featured=True).select_related('category', 'brand').prefetch_related('images')[:8]


class CategoryListView(generics.ListAPIView):
    """GET: List all active categories"""
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    queryset = Category.objects.filter(is_active=True).prefetch_related('children')
    
    def get_queryset(self):
        # Only return parent categories, children will be included in serializer
        return Category.objects.filter(is_active=True, parent=None).prefetch_related('children')


class BrandListView(generics.ListAPIView):
    """GET: List all active brands"""
    serializer_class = BrandSerializer
    permission_classes = [AllowAny]
    queryset = Brand.objects.filter(is_active=True)


class ProductReviewListCreateView(generics.ListCreateAPIView):
    """
    GET: List approved reviews for a product
    POST: Create a new review (authentication optional for demo)
    """
    serializer_class = ProductReviewSerializer
    permission_classes = [AllowAny]  # For demo purposes, change to [IsAuthenticated] in production
    
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        return ProductReview.objects.filter(
            product_id=product_id, 
            is_approved=True
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        product = get_object_or_404(Product, id=product_id)
        serializer.save(product=product)


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """
    GET: Provide search suggestions based on query
    Query parameter: q (search term)
    """
    query = request.query_params.get('q', '').strip()
    
    if not query or len(query) < 2:
        return Response({'suggestions': []})
    
    # Search in products
    products = Product.objects.filter(
        Q(name__icontains=query) | Q(tags__icontains=query),
        is_active=True
    )[:5]
    
    # Search in categories
    categories = Category.objects.filter(
        name__icontains=query,
        is_active=True
    )[:3]
    
    # Search in brands
    brands = Brand.objects.filter(
        name__icontains=query,
        is_active=True
    )[:3]
    
    suggestions = {
        'products': [{'id': p.id, 'name': p.name, 'price': p.price} for p in products],
        'categories': [{'id': c.id, 'name': c.name} for c in categories],
        'brands': [{'id': b.id, 'name': b.name} for b in brands],
    }
    
    return Response({'suggestions': suggestions})


@api_view(['GET'])
@permission_classes([AllowAny])
def product_filters(request):
    """
    GET: Get all available filter options for products
    Used for building dynamic filter UI
    """
    categories = Category.objects.filter(is_active=True).values('id', 'name')
    brands = Brand.objects.filter(is_active=True).values('id', 'name')
    
    # Price range
    price_range = Product.objects.filter(is_active=True).aggregate(
        min_price=Min('price'),
        max_price=Max('price')
    )
    
    # Available sizes and colors from variants
    sizes = ProductVariant.objects.filter(
        is_active=True, 
        product__is_active=True
    ).values_list('size', flat=True).distinct().exclude(size='')
    
    colors = ProductVariant.objects.filter(
        is_active=True, 
        product__is_active=True
    ).values_list('color', flat=True).distinct().exclude(color='')
    
    filters = {
        'categories': list(categories),
        'brands': list(brands),
        'price_range': price_range,
        'sizes': list(sizes),
        'colors': list(colors),
    }
    
    return Response(filters)


@api_view(['GET'])
@permission_classes([AllowAny])
def homepage_data(request):
    """
    GET: Get data for homepage including:
    - Featured products
    - Popular categories
    - Latest products
    - Best selling products (placeholder for now)
    """
    
    # Featured products
    featured_products = Product.objects.filter(
        is_active=True, 
        featured=True
    ).select_related('category', 'brand').prefetch_related('images')[:8]
    
    # Latest products
    latest_products = Product.objects.filter(
        is_active=True
    ).select_related('category', 'brand').prefetch_related('images').order_by('-created_at')[:8]
    
    # Popular categories (categories with most products)
    popular_categories = Category.objects.filter(
        is_active=True
    ).annotate(
        product_count=Count('products')
    ).filter(product_count__gt=0).order_by('-product_count')[:6]
    
    data = {
        'featured_products': ProductListSerializer(featured_products, many=True).data,
        'latest_products': ProductListSerializer(latest_products, many=True).data,
        'popular_categories': CategorySerializer(popular_categories, many=True).data,
        'stats': {
            'total_products': Product.objects.filter(is_active=True).count(),
            'total_categories': Category.objects.filter(is_active=True).count(),
            'total_brands': Brand.objects.filter(is_active=True).count(),
        }
    }
    
    return Response(data)