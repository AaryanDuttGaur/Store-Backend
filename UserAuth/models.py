# from django.db import models
# from django.contrib.auth.models import User
# import uuid

# class CustomerProfile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
#     customer_id = models.CharField(max_length=20, unique=True, editable=False)

#     def save(self, *args, **kwargs):
#         if not self.customer_id:
#             # generate something like "CUST-1A2B3C4D"
#             self.customer_id = "CUST-" + uuid.uuid4().hex[:8].upper()
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.user.username} ({self.customer_id})"
from django.db import models
from django.contrib.auth.models import User
import uuid

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    customer_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Add extended_data field to store additional profile info as JSON
    extended_data = models.TextField(blank=True, null=True, help_text="JSON field for extended profile data")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.customer_id:
            # generate something like "CUST-1A2B3C4D"
            self.customer_id = "CUST-" + uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} ({self.customer_id})"