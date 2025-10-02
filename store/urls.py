# # from django.contrib import admin
# # from django.urls import path, include
# # from django.conf import settings
# # from django.conf.urls.static import static

# # urlpatterns = [
# #     path('admin/', admin.site.urls),
# #     path('api/auth/', include('UserAuth.urls')),      # Authentication endpoints
# #     path('api/account/', include('Account.urls')),    # Account management endpoints
# #     path('api/products/', include('Product.urls')),  # Product management endpoints
# #     path('api/cart/', include('Cart.urls')),         # Cart management endpoints
# #     path('api/orders/', include('Order.urls')),      # Order management endpoints
# # ]

# # # Serve media files during development
# # if settings.DEBUG:
# #     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.http import JsonResponse

# def home(request):
#     return JsonResponse({'message': 'Store Backend API', 'status': 'running'})

# urlpatterns = [
#     path('', home),  # Add this line for root URL
#     path('admin/', admin.site.urls),
#     path('api/auth/', include('UserAuth.urls')),
#     path('api/account/', include('Account.urls')),
#     path('api/products/', include('Product.urls')),
#     path('api/cart/', include('Cart.urls')),
#     path('api/orders/', include('Order.urls')),
# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        'message': 'Store Backend API',
        'status': 'running',
        'endpoints': {
            'admin': '/admin/',
            'auth': '/api/auth/',
            'account': '/api/account/',
            'products': '/api/products/',
            'cart': '/api/cart/',
            'orders': '/api/orders/'
        }
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('UserAuth.urls')),
    path('api/account/', include('Account.urls')),
    path('api/products/', include('Product.urls')),
    path('api/cart/', include('Cart.urls')),
    path('api/orders/', include('Order.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)