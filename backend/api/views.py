from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from scraper.utils import scrape_all_sites, scrape_meesho, scrape_nykaa_fashion, scrape_fabindia
import logging
from django.http import JsonResponse
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password, check_password
from .models import User, SearchHistory, ClothingItem
from .serializers import UserSerializer, UserRegistrationSerializer, SearchHistorySerializer, ClothingItemSerializer
import jwt
from django.conf import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    """
    Search for clothing items across multiple e-commerce sites.
    
    Query parameters:
    - query: The search term (required)
    - sites: Comma-separated list of sites to search (optional, defaults to all)
    - timeout: Maximum time to wait for results in seconds (optional, defaults to 60)
    - min_rating: Minimum rating filter (optional)
    - min_price: Minimum price filter (optional)
    - max_price: Maximum price filter (optional)
    """
    query = request.GET.get('query', '')
    if not query:
        return Response({"error": "Query parameter is required"}, status=400)
    
    sites = request.GET.get('sites', '')
    timeout = int(request.GET.get('timeout', 60))
    min_rating = float(request.GET.get('min_rating', 0))
    min_price = float(request.GET.get('min_price', 0))
    max_price = float(request.GET.get('max_price', float('inf')))
    
    try:
        start_time = time.time()
        results = []
        errors = []
        
        # If specific sites are requested
        if sites:
            site_list = [s.strip().lower() for s in sites.split(',')]
            site_functions = {
                'meesho': scrape_meesho,
                'nykaa': scrape_nykaa_fashion,
                'nykaafashion': scrape_nykaa_fashion,
                'fabindia': scrape_fabindia
            }
            
            with ThreadPoolExecutor(max_workers=len(site_list)) as executor:
                future_to_site = {
                    executor.submit(func, query): site
                    for site, func in site_functions.items()
                    if site in site_list
                }
                
                for future in future_to_site:
                    site = future_to_site[future]
                    try:
                        site_results = future.result(timeout=timeout)
                        results.extend(site_results)
                    except TimeoutError:
                        errors.append(f"Timeout while scraping {site}")
                    except Exception as e:
                        errors.append(f"Error scraping {site}: {str(e)}")
        else:
            # Search all sites
            try:
                results = scrape_all_sites(query)
            except Exception as e:
                errors.append(f"Error in general scraping: {str(e)}")
        
        # Filter out products with missing critical data
        filtered_results = [
            product for product in results 
            if product.get('name') != 'N/A' and product.get('price') is not None
        ]
        
        # Apply filters
        filtered_results = [
            product for product in filtered_results
            if (product.get('price', 0) >= min_price and 
                product.get('price', float('inf')) <= max_price)
        ]
        
        # Apply rating filter if specified
        if min_rating > 0:
            filtered_results = [
                product for product in filtered_results
                if (product.get('rating') and 
                    product.get('rating') != 'N/A' and
                    (float(product.get('rating').split('|')[0] if isinstance(product.get('rating'), str) and '|' in product.get('rating')
                    else product.get('rating').split()[0] if isinstance(product.get('rating'), str)
                    else product.get('rating', 0)) >= min_rating))
            ]
        
        # Sort by price (lowest first)
        sorted_results = sorted(
            filtered_results, 
            key=lambda x: x.get('price', float('inf')) if x.get('price') is not None else float('inf')
        )
        
        execution_time = time.time() - start_time
        
        response_data = {
            "query": query,
            "total_results": len(sorted_results),
            "results": sorted_results,
            "execution_time": round(execution_time, 2),
            "errors": errors if errors else None
        }
        
        # Save search history if user is authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                SearchHistory.objects.create(user=request.user, query=query)
            except Exception as e:
                logger.error(f"Error saving search history: {e}")
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Error in search API: {e}")
        return Response({
            "error": f"An error occurred: {str(e)}",
            "query": query,
            "results": []
        }, status=500)

def home_view(request):
    return JsonResponse({
        "message": "Welcome to the Clothing API",
        "endpoints": {
            "search": "/api/search/",
            "documentation": "Use /api/search/?query=your_search_term to search for clothing items"
        }
    })

def index(request):
    return JsonResponse({
        "message": "Welcome to the Clothing API",
        "available_endpoints": {
            "search": "/api/search/",
            "documentation": "Use /api/search/?query=your_search_term to search for clothing items"
        }
    })

def generate_token(user_id):
    payload = {
        'user_id': str(user_id),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user_data = serializer.validated_data
        user_data['password'] = make_password(user_data['password'])
        user = User.objects.create(**user_data)
        token = generate_token(user.id)
        return Response({
            'token': token,
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    
    try:
        user = User.objects.get(email=email)
        if check_password(password, user.password):
            token = generate_token(user.id)
            return Response({
                'token': token,
                'user': UserSerializer(user).data
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    return Response(UserSerializer(user).data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user_profile(request):
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    
    if not check_password(old_password, user.password):
        return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.password = make_password(new_password)
    user.save()
    return Response({'message': 'Password updated successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_search(request):
    query = request.data.get('query')
    if query:
        SearchHistory.objects.create(user=request.user, query=query)
    return Response({'message': 'Search saved successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_search_history(request):
    searches = SearchHistory.objects.filter(user=request.user).order_by('-created_at')
    serializer = SearchHistorySerializer(searches, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_clothing_item(request, item_id):
    """
    Get detailed information about a specific clothing item.
    """
    try:
        item = get_object_or_404(ClothingItem, id=item_id)
        serializer = ClothingItemSerializer(item)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {"error": f"Error retrieving clothing item: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST
        )
