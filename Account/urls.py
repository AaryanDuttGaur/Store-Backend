from django.urls import path
from .views import ProfileView, DashboardView

urlpatterns = [
    # Main profile endpoint - GET/PUT profile data
    path("profile/", ProfileView.as_view(), name="profile"),
    
    # Dashboard endpoint - GET dashboard stats  
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]