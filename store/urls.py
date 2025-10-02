from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('UserAuth.urls')),      # Authentication endpoints
    path('api/account/', include('Account.urls')),    # Account management endpoints
    path('api/products/', include('Product.urls')),  # Product management endpoints
    path('api/cart/', include('Cart.urls')),         # Cart management endpoints
    path('api/orders/', include('Order.urls')),      # Order management endpoints
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)