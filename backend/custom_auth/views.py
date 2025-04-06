from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import UserRegistrationSerializer, CustomTokenObtainPairSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import UserSerializer
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random
import string

# Create your views here.

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully",
                "user": {
                    "email": user.email,
                    "username": user.username,
                    "phone": user.phone
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "email": user.email,
            "username": user.username,
            "phone": user.phone
        })

@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'error': 'Email not found. Please register first.',
            'should_register': True
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not user.check_password(password):
        return Response({
            'error': 'Invalid password'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': UserSerializer(user).data
    })

def generate_token(length=32):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@api_view(['POST'])
def request_password_reset(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        token = generate_token()
        user.reset_token = token
        user.reset_token_expires = timezone.now() + timedelta(hours=1)
        user.save()
        
        # Send email with reset link
        reset_link = f"http://localhost:5173/reset-password/{token}"
        send_mail(
            'Password Reset Request',
            f'Click the following link to reset your password: {reset_link}',
            'noreply@shopsphere.com',
            [email],
            fail_silently=False,
        )
        return Response({'message': 'Password reset email sent'})
    except User.DoesNotExist:
        return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def reset_password(request, token):
    try:
        user = User.objects.get(reset_token=token)
        if user.reset_token_expires < timezone.now():
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        password = request.data.get('password')
        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        user.save()
        return Response({'message': 'Password reset successful'})
    except User.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def send_verification_email(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    token = generate_token()
    request.user.email_verification_token = token
    request.user.email_verification_token_expires = timezone.now() + timedelta(hours=24)
    request.user.save()
    
    verification_link = f"http://localhost:5173/verify-email/{token}"
    send_mail(
        'Verify Your Email',
        f'Click the following link to verify your email: {verification_link}',
        'noreply@shopsphere.com',
        [request.user.email],
        fail_silently=False,
    )
    return Response({'message': 'Verification email sent'})

@api_view(['POST'])
def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)
        if user.email_verification_token_expires < timezone.now():
            return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_email_verified = True
        user.email_verification_token = None
        user.email_verification_token_expires = None
        user.save()
        return Response({'message': 'Email verified successfully'})
    except User.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
def user_preferences(request):
    if not request.user.is_authenticated:
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if request.method == 'GET':
        return Response({'preferences': request.user.preferences})
    
    preferences = request.data.get('preferences', {})
    request.user.preferences = preferences
    request.user.save()
    return Response({'message': 'Preferences updated successfully'})
