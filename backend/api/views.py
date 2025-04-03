from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from scraper.utils import scrape_all_sites, scrape_meesho, scrape_nykaa_fashion, scrape_fabindia
import logging
from django.http import JsonResponse
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import time

logger = logging.getLogger(__name__)

@api_view(['GET'])
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
