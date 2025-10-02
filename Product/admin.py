from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
from django.middleware.csrf import get_token
import csv
import io
import requests
from django.core.files.base import ContentFile
from urllib.parse import urlparse
import os

from .models import (
    Category, Brand, Product, ProductImage, ProductVariant, 
    ProductReview, ProductAttribute
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ('name', 'sku', 'price', 'quantity', 'color', 'size', 'is_active')


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    fields = ('name', 'value', 'sort_order')


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('customer_name', 'rating', 'title', 'review', 'created_at')
    can_delete = True
    fields = ('customer_name', 'rating', 'title', 'is_approved', 'is_verified')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'sort_order', 'product_count', 'created_at')
    list_filter = ('is_active', 'parent', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active', 'sort_order')
    ordering = ('sort_order', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'slug', 'parent')
        }),
        ('Display', {
            'fields': ('image', 'is_active', 'sort_order')
        }),
    )
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = "Products"


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'product_count', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'website')
        }),
        ('Display', {
            'fields': ('logo', 'is_active')
        }),
    )
    
    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = "Products"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'sku', 'category', 'brand', 'price', 'stock_status', 
        'is_active', 'featured', 'created_at'
    )
    list_filter = (
        'is_active', 'featured', 'category', 'brand', 'track_quantity', 
        'created_at', 'is_digital'
    )
    search_fields = ('name', 'sku', 'description', 'tags')
    list_editable = ('is_active', 'featured', 'price')
    readonly_fields = (
        'sku', 'slug', 'created_at', 'updated_at', 'stock_status', 
        'discount_info', 'main_image_preview'
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'sku', 'slug', 'short_description', 'description', 
                'category', 'brand', 'tags'
            )
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost_price', 'discount_info'),
            'classes': ('collapse',)
        }),
        ('Inventory', {
            'fields': (
                'track_quantity', 'quantity', 'low_stock_threshold', 
                'allow_backorder', 'stock_status'
            ),
        }),
        ('Physical Properties', {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('SEO & Marketing', {
            'fields': ('meta_title', 'meta_description', 'featured'),
            'classes': ('collapse',)
        }),
        ('Product Type', {
            'fields': ('is_digital', 'requires_shipping'),
            'classes': ('collapse',)
        }),
        ('Status & Dates', {
            'fields': ('is_active', 'published_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Main Image Preview', {
            'fields': ('main_image_preview',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline, ProductVariantInline, ProductAttributeInline, ProductReviewInline]
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured', 'export_csv']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.import_csv_view, name='product_import_csv'),
        ]
        return custom_urls + urls
    
    def import_csv_view(self, request):
        """CSV Import functionality with image URL support"""
        if request.method == 'POST' and request.FILES.get('csv_file'):
            csv_file = request.FILES['csv_file']
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a CSV file.')
                return redirect('..')
            
            try:
                decoded_file = csv_file.read().decode('utf-8')
                csv_data = csv.DictReader(io.StringIO(decoded_file))
                
                created_count = 0
                error_count = 0
                errors = []
                
                for row_num, row in enumerate(csv_data, 1):
                    try:
                        # Get or create category
                        category_name = row.get('category', '').strip()
                        if category_name:
                            category, _ = Category.objects.get_or_create(
                                name=category_name,
                                defaults={'slug': category_name.lower().replace(' ', '-')}
                            )
                        else:
                            category = None
                        
                        # Get or create brand
                        brand_name = row.get('brand', '').strip()
                        brand = None
                        if brand_name:
                            brand, _ = Brand.objects.get_or_create(name=brand_name)
                        
                        # Create product
                        product_data = {
                            'name': row.get('name', '').strip(),
                            'description': row.get('description', '').strip(),
                            'short_description': row.get('short_description', '').strip(),
                            'price': float(row.get('price', 0)) if row.get('price') else 0,
                            'compare_price': float(row.get('compare_price', 0)) if row.get('compare_price') else None,
                            'quantity': int(row.get('quantity', 0)) if row.get('quantity') else 0,
                            'weight': float(row.get('weight', 0)) if row.get('weight') else None,
                            'tags': row.get('tags', '').strip(),
                            'category': category,
                            'brand': brand,
                            'is_active': row.get('is_active', 'True').lower() == 'true',
                            'featured': row.get('featured', 'False').lower() == 'true',
                        }
                        
                        product = Product.objects.create(**product_data)
                        
                        # Handle image URL if provided
                        image_url = row.get('image_url', '').strip()
                        if image_url:
                            try:
                                # Download image with timeout
                                headers = {
                                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                }
                                response = requests.get(image_url, headers=headers, timeout=15)
                                
                                if response.status_code == 200:
                                    # Get filename from URL or create one
                                    parsed_url = urlparse(image_url)
                                    filename = os.path.basename(parsed_url.path)
                                    
                                    # If no filename in URL, create one
                                    if not filename or '.' not in filename:
                                        content_type = response.headers.get('content-type', '')
                                        if 'jpeg' in content_type or 'jpg' in content_type:
                                            extension = '.jpg'
                                        elif 'png' in content_type:
                                            extension = '.png'
                                        elif 'webp' in content_type:
                                            extension = '.webp'
                                        else:
                                            extension = '.jpg'  # default
                                        filename = f"product_{product.id}{extension}"
                                    
                                    # Create ProductImage
                                    product_image = ProductImage(
                                        product=product,
                                        alt_text=f"Image for {product.name}",
                                        is_main=True,
                                        sort_order=0
                                    )
                                    
                                    # Save image file
                                    product_image.image.save(
                                        filename,
                                        ContentFile(response.content),
                                        save=True
                                    )
                                else:
                                    errors.append(f"Row {row_num}: Could not download image (HTTP {response.status_code})")
                                    
                            except requests.exceptions.RequestException as img_error:
                                errors.append(f"Row {row_num}: Image download failed - {str(img_error)}")
                            except Exception as img_error:
                                errors.append(f"Row {row_num}: Image processing error - {str(img_error)}")
                        
                        created_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {row_num}: {str(e)}")
                
                # Show results
                if created_count > 0:
                    messages.success(request, f'Successfully imported {created_count} products.')
                
                if error_count > 0:
                    error_msg = f'{error_count} errors occurred:\n' + '\n'.join(errors[:10])
                    if len(errors) > 10:
                        error_msg += f'\n... and {len(errors) - 10} more errors.'
                    messages.error(request, error_msg)
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
            
            return redirect('..')
        
        # Return inline HTML form with updated instructions
        csrf_token = get_token(request)
        
        html_form = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Import Products CSV</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                       margin: 40px; background: #f8f9fa; }}
                .container {{ max-width: 900px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #2c3e50; margin-bottom: 20px; }}
                .form-group {{ margin: 20px 0; }}
                input[type="file"] {{ padding: 10px; border: 2px dashed #ddd; border-radius: 4px; width: 100%; }}
                .btn {{ background: #007cba; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
                .btn:hover {{ background: #005a87; }}
                .cancel {{ background: #666; margin-left: 10px; text-decoration: none; padding: 12px 24px; color: white; border-radius: 4px; }}
                .instructions {{ margin-top: 30px; padding: 20px; background: #e8f4f8; border-radius: 4px; }}
                .example {{ font-family: monospace; background: #f4f4f4; padding: 10px; border-radius: 4px; margin: 10px 0; font-size: 12px; overflow-x: auto; }}
                .new-feature {{ background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 4px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Import Products from CSV (with Images)</h1>
                
                <div class="new-feature">
                    <strong>NEW:</strong> You can now include image URLs in your CSV! Add an "image_url" column with direct links to product images.
                </div>
                
                <form method="post" enctype="multipart/form-data">
                    <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                    <div class="form-group">
                        <label for="csv_file"><strong>Choose CSV file:</strong></label><br><br>
                        <input type="file" name="csv_file" id="csv_file" accept=".csv" required>
                    </div>
                    <div class="form-group">
                        <input type="submit" value="Import Products with Images" class="btn">
                        <a href="../" class="cancel">Cancel</a>
                    </div>
                </form>
                
                <div class="instructions">
                    <h3>CSV Format Required:</h3>
                    <p><strong>Required Headers (with optional image_url):</strong></p>
                    <div class="example">name,description,short_description,price,compare_price,quantity,category,brand,is_active,featured,tags,weight,image_url</div>
                    
                    <p><strong>Example Row:</strong></p>
                    <div class="example">iPhone 15,"Apple iPhone 15 smartphone","Latest iPhone",799.99,899.99,25,Electronics,Apple,True,True,"smartphone,iphone",0.172,https://example.com/iphone.jpg</div>
                    
                    <h4>Notes:</h4>
                    <ul>
                        <li><strong>name, price:</strong> Required fields</li>
                        <li><strong>category, brand:</strong> Will be created if they don't exist</li>
                        <li><strong>is_active, featured:</strong> Use True/False</li>
                        <li><strong>image_url:</strong> Optional. Direct link to product image (jpg, png, webp)</li>
                        <li><strong>Image requirements:</strong> Public URLs, under 10MB, common formats</li>
                        <li><strong>Image errors:</strong> Products will still be created even if image download fails</li>
                    </ul>
                    
                    <h4>Supported Image Sources:</h4>
                    <ul>
                        <li>Direct image URLs (https://example.com/image.jpg)</li>
                        <li>Unsplash (https://images.unsplash.com/...)</li>
                        <li>Your CDN or file hosting service</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_form)
    
    def stock_status(self, obj):
        if not obj.track_quantity:
            return format_html('<span style="color: #27ae60;">✓ Always Available</span>')
        
        if obj.quantity <= 0:
            return format_html('<span style="color: #e74c3c;">✗ Out of Stock</span>')
        elif obj.is_low_stock:
            return format_html(
                '<span style="color: #f39c12;">⚠ Low Stock ({})</span>', 
                obj.quantity
            )
        else:
            return format_html(
                '<span style="color: #27ae60;">✓ In Stock ({})</span>', 
                obj.quantity
            )
    stock_status.short_description = "Stock"
    
    def discount_info(self, obj):
        if obj.is_on_sale:
            return f"{obj.discount_percentage}% OFF"
        return "No discount"
    discount_info.short_description = "Discount"
    
    def main_image_preview(self, obj):
        main_img = obj.main_image
        if main_img:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                main_img.url
            )
        return "No main image"
    main_image_preview.short_description = "Main Image"
    
    # Actions
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        messages.success(request, f'{updated} products marked as active.')
    make_active.short_description = "Mark selected products as active"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        messages.success(request, f'{updated} products marked as inactive.')
    make_inactive.short_description = "Mark selected products as inactive"
    
    def make_featured(self, request, queryset):
        updated = queryset.update(featured=True)
        messages.success(request, f'{updated} products marked as featured.')
    make_featured.short_description = "Mark selected products as featured"
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(featured=False)
        messages.success(request, f'{updated} products removed from featured.')
    remove_featured.short_description = "Remove selected products from featured"
    
    def export_csv(self, request, queryset):
        """Export products to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'name', 'sku', 'description', 'price', 'compare_price', 'quantity',
            'category', 'brand', 'is_active', 'featured', 'tags', 'created_at'
        ])
        
        for product in queryset:
            writer.writerow([
                product.name, product.sku, product.description, product.price,
                product.compare_price, product.quantity,
                product.category.name if product.category else '',
                product.brand.name if product.brand else '',
                product.is_active, product.featured, product.tags, product.created_at
            ])
        
        return response
    export_csv.short_description = "Export selected products to CSV"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'alt_text', 'is_main', 'sort_order')
    list_filter = ('is_main', 'created_at')
    search_fields = ('product__name', 'alt_text')
    list_editable = ('is_main', 'sort_order')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px;" />',
                obj.image.url
            )
        return "No image"
    image_preview.short_description = "Preview"


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'sku', 'effective_price', 'quantity', 'is_active')
    list_filter = ('is_active', 'color', 'size', 'created_at')
    search_fields = ('product__name', 'name', 'sku')
    list_editable = ('quantity', 'is_active')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'customer_name', 'rating', 'title', 'is_approved', 'is_verified', 'created_at')
    list_filter = ('rating', 'is_approved', 'is_verified', 'created_at')
    search_fields = ('product__name', 'customer_name', 'title', 'review')
    list_editable = ('is_approved', 'is_verified')
    readonly_fields = ('created_at',)
    
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        messages.success(request, f'{updated} reviews approved.')
    approve_reviews.short_description = "Approve selected reviews"
    
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        messages.success(request, f'{updated} reviews unapproved.')
    unapprove_reviews.short_description = "Unapprove selected reviews"


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'value', 'sort_order')
    list_filter = ('name', 'product__category')
    search_fields = ('product__name', 'name', 'value')
    list_editable = ('sort_order',)


# Admin site customization
admin.site.site_header = "E-commerce Product Management"
admin.site.site_title = "Product Admin"
admin.site.index_title = "Manage Your Products"