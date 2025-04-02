from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Root URL handler
    path('search/', views.search, name='search'),  # Search endpoint
]
