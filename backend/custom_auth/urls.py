from django.urls import path
from .views import UserRegistrationView, CustomTokenObtainPairView, UserProfileView
from . import views

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('reset-password/', views.request_password_reset, name='request_password_reset'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('verify-email/', views.send_verification_email, name='send_verification_email'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('preferences/', views.user_preferences, name='user_preferences'),
] 