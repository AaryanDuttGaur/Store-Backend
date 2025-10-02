from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from UserAuth.models import CustomerProfile
from UserAuth.serializers import UserSerializer
from datetime import datetime
import json


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET: Fetch user profile data by customer_id
    PUT: Update user profile data
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get(self, request, *args, **kwargs):
        """Fetch profile data based on logged user's customer_id"""
        user = self.get_object()
        
        try:
            customer_profile = user.profile
            
            # Get or create extended profile data (stored as JSON for now)
            extended_data = {}
            if hasattr(customer_profile, 'extended_data') and customer_profile.extended_data:
                try:
                    extended_data = json.loads(customer_profile.extended_data)
                except:
                    extended_data = {}
            
            profile_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'customer_id': customer_profile.customer_id,
                
                # Extended profile fields from JSON storage
                'phone': extended_data.get('phone', ''),
                'date_of_birth': extended_data.get('date_of_birth', ''),
                'gender': extended_data.get('gender', ''),
                'address': extended_data.get('address', {
                    'street': '',
                    'city': '',
                    'state': '',
                    'postal_code': '',
                    'country': ''
                }),
                
                'member_since': user.date_joined.strftime('%B %Y') if user.date_joined else 'Recently joined',
                'is_active': user.is_active
            }
            
            return Response(profile_data, status=status.HTTP_200_OK)
            
        except CustomerProfile.DoesNotExist:
            return Response(
                {'detail': 'Customer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Error fetching profile: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, *args, **kwargs):
        """Update profile data for logged user's customer_id"""
        user = self.get_object()
        
        try:
            customer_profile = user.profile
            
            # Update basic user fields
            user.first_name = request.data.get('first_name', user.first_name)
            user.last_name = request.data.get('last_name', user.last_name)
            user.email = request.data.get('email', user.email)
            user.username = request.data.get('username', user.username)
            user.save()
            
            # Prepare extended data to save as JSON
            extended_data = {
                'phone': request.data.get('phone', ''),
                'date_of_birth': request.data.get('date_of_birth', ''),
                'gender': request.data.get('gender', ''),
                'address': request.data.get('address', {
                    'street': '',
                    'city': '',
                    'state': '',
                    'postal_code': '',
                    'country': ''
                })
            }
            
            # Save extended data as JSON in CustomerProfile
            # First, we need to add extended_data field to CustomerProfile model
            if not hasattr(customer_profile, 'extended_data'):
                # For now, we'll use a different approach - update the model file
                pass
            
            # For immediate fix, let's save it differently
            # You'll need to run: python manage.py makemigrations and python manage.py migrate
            try:
                customer_profile.extended_data = json.dumps(extended_data)
                customer_profile.save()
            except Exception as e:
                # If extended_data field doesn't exist, return error message
                return Response(
                    {'detail': 'Database needs to be updated. Please run: python manage.py makemigrations && python manage.py migrate'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Prepare response with updated data
            updated_profile_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'customer_id': customer_profile.customer_id,
                'phone': extended_data['phone'],
                'date_of_birth': extended_data['date_of_birth'],
                'gender': extended_data['gender'],
                'address': extended_data['address'],
                'member_since': user.date_joined.strftime('%B %Y') if user.date_joined else 'Recently joined',
                'is_active': user.is_active
            }
            
            return Response(updated_profile_data, status=status.HTTP_200_OK)
            
        except CustomerProfile.DoesNotExist:
            return Response(
                {'detail': 'Customer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Error updating profile: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DashboardView(generics.GenericAPIView):
    """
    GET: Fetch dashboard data for logged user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Fetch dashboard statistics for logged user's customer_id"""
        user = request.user
        
        try:
            customer_profile = user.profile
            
            dashboard_data = {
                'user_info': {
                    'username': user.username,
                    'customer_id': customer_profile.customer_id,
                    'member_since': user.date_joined.strftime('%B %Y') if user.date_joined else 'Recently joined'
                },
                'orders_count': 0,
                'wishlist_count': 0, 
                'reviews_count': 0,
                'total_spent': 0.0,
                'recent_activity': []
            }
            
            return Response(dashboard_data, status=status.HTTP_200_OK)
            
        except CustomerProfile.DoesNotExist:
            return Response(
                {'detail': 'Customer profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'detail': f'Error fetching dashboard data: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )