from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from api.models import User, SearchHistory
from scraper.utils import scrape_all_sites
import json
import re
from django.contrib.auth.hashers import make_password, check_password

def validate_phone(phone):
    """Validate phone number format."""
    pattern = r'^\+?91?\d{10}$'
    return bool(re.match(pattern, phone))

def validate_password(password):
    """Validate password strength."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """Handle user registration."""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')

        # Validate inputs
        if not all([email, name, phone, password]):
            return JsonResponse({
                'success': False,
                'message': 'All fields are required'
            }, status=400)

        if not validate_phone(phone):
            return JsonResponse({
                'success': False,
                'message': 'Invalid phone number format'
            }, status=400)

        if not validate_password(password):
            return JsonResponse({
                'success': False,
                'message': 'Password must be at least 8 characters long and contain uppercase, lowercase, and numbers'
            }, status=400)

        # Check for existing user
        if User.objects.filter(phone=phone).exists():
            return JsonResponse({
                'success': False,
                'message': 'Phone number already registered'
            }, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'message': 'Email already registered'
            }, status=400)

        # Create user
        user = User.objects.create(
            email=email,
            name=name,
            phone=phone,
            password=make_password(password)
        )

        # Set session
        request.session['user_id'] = str(user.user_id)
        request.session['user_name'] = user.name

        return JsonResponse({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def login(request):
    """Handle user login."""
    try:
        data = json.loads(request.body)
        phone = data.get('phone')
        password = data.get('password')

        if not all([phone, password]):
            return JsonResponse({
                'success': False,
                'message': 'Phone and password are required'
            }, status=400)

        try:
            user = User.objects.get(phone=phone)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid phone number or password'
            }, status=401)

        if not check_password(password, user.password):
            return JsonResponse({
                'success': False,
                'message': 'Invalid phone number or password'
            }, status=401)

        # Set session
        request.session['user_id'] = str(user.user_id)
        request.session['user_name'] = user.name

        return JsonResponse({
            'success': True,
            'message': 'Login successful',
            'user': {
                'name': user.name,
                'email': user.email,
                'phone': user.phone
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@require_http_methods(["POST"])
def logout(request):
    """Handle user logout."""
    request.session.flush()
    return JsonResponse({
        'success': True,
        'message': 'Logout successful'
    })

@require_http_methods(["GET"])
def check_auth(request):
    """Check if user is authenticated."""
    user_id = request.session.get('user_id')
    if user_id:
        try:
            user = User.objects.get(user_id=user_id)
            return JsonResponse({
                'success': True,
                'authenticated': True,
                'user': {
                    'name': user.name,
                    'email': user.email,
                    'phone': user.phone
                }
            })
        except User.DoesNotExist:
            request.session.flush()
            return JsonResponse({
                'success': True,
                'authenticated': False
            })
    return JsonResponse({
        'success': True,
        'authenticated': False
    }) 