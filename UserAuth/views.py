from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer
# signup view
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        # validate request with RegisterSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # return UserSerializer (includes customer_id)
        user_data = UserSerializer(user).data
        return Response(user_data, status=status.HTTP_201_CREATED)

# login view



class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        # validate request with RegisterSerializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # return UserSerializer (includes customer_id)
        user_data = UserSerializer(user).data
        return Response(user_data, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        # Validate input
        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # User exists and password is correct
            if user.is_active:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                # Get user data with customer_id
                user_data = UserSerializer(user).data

                return Response({
                    'message': 'Login successful',
                    'access': str(access_token),
                    'refresh': str(refresh),
                    'user': user_data
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'detail': 'Account is disabled.'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            # Invalid credentials
            return Response(
                {'detail': 'Invalid username or password.'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )