from django.urls import path
from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/profile/', views.get_user_profile, name='profile'),
    path('auth/profile/update/', views.update_user_profile, name='update_profile'),
    path('auth/change-password/', views.change_password, name='change_password'),
    
    # Search history endpoints
    path('search/history/', views.get_search_history, name='search_history'),
    path('search/save/', views.save_search, name='save_search'),
    
    # Search endpoints
    path('search/', views.search, name='search'),
    path('clothing/<str:item_id>/', views.get_clothing_item, name='get_clothing_item'),
]
