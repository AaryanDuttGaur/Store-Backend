from django.contrib import admin
from .models import CustomerProfile
from django.contrib.auth.models import User

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'customer_id', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'customer_id', 'user__email')
    readonly_fields = ('customer_id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('User Info', {
            'fields': ('user', 'customer_id')
        }),
        ('Extended Data', {
            'fields': ('extended_data',),
            'description': 'JSON stored profile data'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields