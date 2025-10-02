from rest_framework import serializers
from .models import (
    Product, Category, Brand, ProductImage, ProductVariant, 
    ProductReview, ProductAttribute
)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories with hierarchical support"""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'slug', 'image', 'parent', 
            'children', 'product_count', 'full_path', 'is_active', 'sort_order'
        ]
    
    def get_children(self, obj):
        """Get child categories"""
        if obj.children.filter(is_active=True).exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []
    
    def get_product_count(self, obj):
        """Get number of active products in this category"""
        return obj.products.filter(is_active=True).count()
    
    def get_full_path(self, obj):
        """Get full category path"""
        return obj.get_full_path()


class BrandSerializer(serializers.ModelSerializer):
    """Serializer for product brands"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ['id', 'name', 'description', 'logo', 'website', 'product_count']
    
    def get_product_count(self, obj):
        """Get number of active products for this brand"""
        return obj.product_set.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer for product images"""
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_main', 'sort_order']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for product variants"""
    effective_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price', 'effective_price', 'quantity', 
            'color', 'size', 'material', 'is_active'
        ]


class ProductAttributeSerializer(serializers.ModelSerializer):
    """Serializer for product attributes/specifications"""
    
    class Meta:
        model = ProductAttribute
        fields = ['id', 'name', 'value', 'sort_order']


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews"""
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'customer_name', 'customer_email', 'rating', 'title', 
            'review', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']
    
    def create(self, validated_data):
        """Create a new review (will need approval in admin)"""
        validated_data['is_approved'] = False  # Require admin approval
        return super().create(validated_data)


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists (shop page, search results)"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'short_description', 'sku', 'slug', 'price', 'compare_price',
            'category', 'brand', 'main_image', 'is_on_sale', 'discount_percentage',
            'is_in_stock', 'is_low_stock', 'featured', 'average_rating', 'review_count',
            'created_at'
        ]
    
    def get_main_image(self, obj):
        """Get the main product image URL"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None
    
    def get_average_rating(self, obj):
        """Get average rating from approved reviews"""
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return 0
    
    def get_review_count(self, obj):
        """Get count of approved reviews"""
        return obj.reviews.filter(is_approved=True).count()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for detailed product view"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    
    # Computed fields
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    main_image = serializers.SerializerMethodField()
    
    # Additional product info
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'short_description', 'sku', 'slug',
            'price', 'compare_price', 'cost_price', 'category', 'brand', 'tags',
            'quantity', 'track_quantity', 'low_stock_threshold', 'allow_backorder',
            'weight', 'length', 'width', 'height', 'meta_title', 'meta_description',
            'is_digital', 'requires_shipping', 'featured', 'is_active',
            'created_at', 'updated_at', 'published_at',
            
            # Relationships
            'images', 'variants', 'attributes', 'reviews',
            
            # Computed fields
            'is_on_sale', 'discount_percentage', 'is_in_stock', 'is_low_stock',
            'main_image', 'average_rating', 'review_count'
        ]
    
    def get_main_image(self, obj):
        """Get the main product image URL"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None
    
    def get_reviews(self, obj):
        """Get recent approved reviews (limit for performance)"""
        recent_reviews = obj.reviews.filter(is_approved=True).order_by('-created_at')[:5]
        return ProductReviewSerializer(recent_reviews, many=True).data
    
    def get_average_rating(self, obj):
        """Get average rating from approved reviews"""
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(avg=models.Avg('rating'))['avg'], 1)
        return 0
    
    def get_review_count(self, obj):
        """Get count of approved reviews"""
        return obj.reviews.filter(is_approved=True).count()


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating products (admin use)"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category', 'brand',
            'price', 'compare_price', 'cost_price', 'quantity', 'track_quantity',
            'low_stock_threshold', 'allow_backorder', 'weight', 'length', 
            'width', 'height', 'tags', 'meta_title', 'meta_description',
            'is_digital', 'requires_shipping', 'featured', 'is_active'
        ]
    
    def validate_price(self, value):
        """Validate that price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_compare_price(self, value):
        """Validate that compare price is higher than regular price"""
        if value and hasattr(self, 'initial_data'):
            price = self.initial_data.get('price')
            if price and float(value) <= float(price):
                raise serializers.ValidationError(
                    "Compare price must be higher than regular price."
                )
        return value
    
    def validate_quantity(self, value):
        """Validate quantity is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative.")
        return value


class FeaturedProductSerializer(serializers.ModelSerializer):
    """Minimal serializer for featured products on homepage"""
    main_image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_on_sale = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'short_description', 'slug', 'price', 'compare_price',
            'main_image', 'category_name', 'is_on_sale', 'discount_percentage'
        ]
    
    def get_main_image(self, obj):
        """Get the main product image URL"""
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(main_image.image.url)
            return main_image.image.url
        return None


class SearchSuggestionSerializer(serializers.ModelSerializer):
    """Minimal serializer for search suggestions"""
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'slug']


# Import models for aggregation functions
from django.db import models