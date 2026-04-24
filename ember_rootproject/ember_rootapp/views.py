import os

from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import json

from .models import BusinessHours, ContactMessage, MenuItem, User, Pizza, Order, Favorite, UserActivity, UserSession
from .forms import (
    ContactForm,
    CustomAuthenticationForm, 
    CustomUserCreationForm,
    ProfileUpdateForm,
    EmailUpdateForm,
    CustomPasswordChangeForm,
    ForgotPasswordForm
)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def delete_media_file(file_url):
    """Delete a media file from the filesystem."""
    if not file_url:
        return False
    
    # Only handle local media files
    if file_url.startswith('/media/'):
        try:
            # Use MEDIA_ROOT from settings
            relative_path = file_url.replace('/media/', '', 1)
            file_path = settings.MEDIA_ROOT / relative_path
            
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted media file: {file_path}")
                return True
            else:
                print(f"Media file not found: {file_path}")
                return False
        except Exception as e:
            print(f"Error deleting media file {file_url}: {e}")
            return False
    
    # Not a local media file (might be external URL)
    return False


def log_user_activity(user, activity_type, description='', request=None):
    """Log user activity."""
    activity = UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )
    return activity


# ==================== Authentication Views ====================

def auth_view(request):
    """
    Combined authentication view for login and registration.
    Handles both forms on the same page.
    """
    if request.user.is_authenticated:
        if request.user.is_admin_user or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    
    login_form = CustomAuthenticationForm()
    register_form = CustomUserCreationForm()
    
    context = {
        'login_form': login_form,
        'register_form': register_form,
    }
    
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        
        if form_type == 'login':
            login_form = CustomAuthenticationForm(data=request.POST)
            login_form = CustomAuthenticationForm(data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()
                user.last_login_at = timezone.now()
                user.save(update_fields=['last_login_at'])
                login(request, user)
                log_user_activity(user, 'login', f'User logged in', request)
                messages.success(request, f'Welcome back, {user.first_name or user.email}! 🍕')
                
                # Redirect admin users to admin dashboard
                if user.is_admin_user or user.is_superuser:
                    return redirect('admin_dashboard')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
                context['login_form'] = login_form
                context['active_tab'] = 'login'
                
        elif form_type == 'register':
            register_form = CustomUserCreationForm(request.POST)
            if register_form.is_valid():
                user = register_form.save(commit=False)
                user.user_type = 'customer'  # Ensure user_type is set
                user.save()
                
                # Log activity
                log_user_activity(
                    user,
                    'register',
                    f'New user registered',
                    request
                )
                
                # Log the user in
                login(request, user)
                
                messages.success(request, f'Welcome to Ember & Root, {user.first_name}! 🔥')
                return redirect('dashboard')
            else:
                context['register_form'] = register_form
                context['active_tab'] = 'register'
    
    return render(request, 'ember_rootapp/auth.html', context)


@require_POST
def ajax_login(request):
    """AJAX login endpoint."""
    if request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Already logged in'})
    
    data = json.loads(request.body)
    email = data.get('email', '').lower()
    password = data.get('password', '')
    
    user = authenticate(request, username=email, password=password)
    
    if user is not None:
        user.last_login_at = timezone.now()
        user.save(update_fields=['last_login_at'])
        login(request, user)
        
        log_user_activity(user, 'login', 'AJAX login', request)
        
        # return JsonResponse({
        #     'success': True,
        #     'message': f'Welcome back, {user.first_name or user.email}!',
        #     'redirect_url': reverse('dashboard')
        # })
        return JsonResponse({
            'success': True,
            'message': f'Welcome back, {user.first_name or user.email}!',
            'redirect_url': reverse('dashboard'),
            'user': {
                'name': user.first_name or user.email,
                'initial': user.get_avatar_initial() # Ensure this method exists on your User model
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid email or password.'
        })


@require_POST
def ajax_register(request):
    """AJAX registration endpoint."""
    if request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'Already logged in'})
    
    data = json.loads(request.body)
    
    form = CustomUserCreationForm({
        'first_name': data.get('name', ''),
        'email': data.get('email', '').lower(),
        'phone': data.get('phone', ''),
        'password1': data.get('password', ''),
        'password2': data.get('confirm_password', ''),
        'terms_agree': data.get('terms_agree', False),
    })
    
    if form.is_valid():
        user = form.save()
        login(request, user)
        
        log_user_activity(user, 'register', 'AJAX registration', request)
        
        return JsonResponse({
            'success': True,
            'message': f'Welcome to Ember & Root, {user.first_name}! 🔥',
            'redirect_url': reverse('dashboard')
        })
    else:
        errors = {}
        for field, error_list in form.errors.items():
            errors[field] = error_list[0]
        return JsonResponse({
            'success': False,
            'message': 'Please correct the errors below.',
            'errors': errors
        })


def logout_view(request):
    """Log out the user."""
    if request.user.is_authenticated:
        log_user_activity(request.user, 'logout', 'User logged out', request)
        logout(request)
        messages.success(request, 'You have been logged out successfully.')
    return redirect('index')


# ==================== Page Views ====================

def index(request):
    """Home page view."""
    # Get featured pizzas (bestsellers)
    featured_pizzas = Pizza.objects.filter(
        is_available=True, 
        bestseller=True
    )[:3]
    
    # If not enough bestsellers, add more pizzas
    if featured_pizzas.count() < 3:
        additional = Pizza.objects.filter(
            is_available=True
        ).exclude(
            id__in=featured_pizzas.values_list('id', flat=True)
        )[:3 - featured_pizzas.count()]
        featured_pizzas = list(featured_pizzas) + list(additional)
    
    context = {
        'featured_pizzas': featured_pizzas,
    }
    return render(request, 'ember_rootapp/index.html', context)


@login_required
def dashboard(request):
    """User dashboard view."""
    user = request.user
    
    # Get user stats
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(
        user=user, 
        status='completed'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    favorite_count = Favorite.objects.filter(user=user).count()
    
    # Get recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')
    
    # Get recent activities
    recent_activities = UserActivity.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    # Get favorite pizzas
    favorites = Favorite.objects.filter(
        user=user
    ).select_related('pizza').order_by('-created_at')
    
    # Get user's contact messages with replies
    user_messages = ContactMessage.objects.filter(
        Q(user=user) | Q(email=user.email)
    ).exclude(
        reply__isnull=True
    ).exclude(
        reply=''
    ).order_by('-replied_at')

    # Count unread replied messages for the badge
    unread_replies_count = user_messages.filter(read_by_user=False).count()
    
    # Determine active tab
    active_tab = request.GET.get('tab', 'overview')
    
    # Prepare JSON data for JavaScript
    import json
    user_data = {
        'full_name': user.get_full_name() or user.email,
        'email': user.email,
        'phone': user.phone or '',
        'avatar': user.get_avatar_initial(),
    }
    
    stats_data = {
        'total_orders': total_orders,
        'total_spent': float(total_spent),
        'favorite_count': favorite_count,
    }
    
    context = {
        'user': user,
        'total_orders': total_orders,
        'total_spent': total_spent,
        'favorite_count': favorite_count,
        'recent_orders': recent_orders,
        'recent_activities': recent_activities,
        'favorites': favorites,
        'user_messages': user_messages[:5], 
        'unread_replies_count': unread_replies_count,
        'member_since': user.created_at,
        'active_tab': active_tab,
        'user_data': json.dumps(user_data),
        'stats_data': json.dumps(stats_data),
    }
    return render(request, 'ember_rootapp/dashboard.html', context)

@login_required
@require_POST
def update_profile(request):
    """Update user profile."""
    user = request.user
    field = request.POST.get('field')
    value = request.POST.get('value', '').strip()
    
    valid_fields = ['first_name', 'last_name', 'phone']
    
    if field not in valid_fields:
        return JsonResponse({'success': False, 'message': 'Invalid field'})
    
    setattr(user, field, value)
    user.save(update_fields=[field, 'updated_at'])
    
    log_user_activity(
        user,
        'profile_update',
        f'Updated {field}',
        request
    )
    
    return JsonResponse({
        'success': True,
        'message': f'{field.replace("_", " ").title()} updated successfully',
        'value': value
    })


@login_required
@require_POST
def update_email(request):
    """Update user email."""
    user = request.user
    form = EmailUpdateForm(request.POST, instance=user)
    
    if form.is_valid():
        user.email = form.cleaned_data['email']
        user.username = user.email
        user.save()
        
        log_user_activity(user, 'profile_update', 'Updated email', request)
        
        return JsonResponse({
            'success': True,
            'message': 'Email updated successfully'
        })
    
    return JsonResponse({
        'success': False,
        'message': form.errors.get('email', ['Invalid email'])[0]
    })


@login_required
@require_POST
def change_password(request):
    """Change user password."""
    user = request.user
    form = CustomPasswordChangeForm(user, request.POST)
    
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        
        log_user_activity(user, 'password_change', 'Password changed', request)
        
        return JsonResponse({
            'success': True,
            'message': 'Password changed successfully'
        })
    
    errors = {}
    for field, error_list in form.errors.items():
        errors[field] = error_list[0]
    
    return JsonResponse({
        'success': False,
        'message': 'Please correct the errors',
        'errors': errors
    })


@login_required
@require_POST
def delete_account(request):
    """Delete user account."""
    # Check if admin is deleting another user
    if request.user.is_admin_user or request.user.is_superuser:
        user_id = json.loads(request.body).get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
            user.delete()
            return JsonResponse({
                'success': True,
                'message': f'Customer account deleted successfully'
            })
    
    # Regular user deleting their own account
    user = request.user
    password = request.POST.get('password', '') or json.loads(request.body).get('password', '')
    
    if not user.check_password(password):
        return JsonResponse({
            'success': False,
            'message': 'Incorrect password'
        })
    
    log_user_activity(user, 'profile_update', 'Account deleted', request)
    user.delete()
    logout(request)
    
    return JsonResponse({
        'success': True,
        'message': 'Your account has been deleted',
        'redirect_url': reverse('index')
    })


def menu(request):
    """Menu page view."""
    # Try to get cached data
    cache_key = 'menu_data'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return render(request, 'ember_rootapp/menu.html', cached_data)
    
    # Get available pizzas
    pizzas = Pizza.objects.filter(is_available=True)
    
    # Get sides
    sides = MenuItem.objects.filter(category='sides', is_available=True)
    
    # Get drinks
    drinks = MenuItem.objects.filter(category='drinks', is_available=True)
    
    # Prepare pizza data for JavaScript
    import json
    pizzas_data = []
    for pizza in pizzas:
        pizzas_data.append({
            'id': pizza.id,
            'name': pizza.name,
            'category': pizza.category,
            'description': pizza.description,
            'price': pizza.price,
            'calories': pizza.calories,
            'dietary': pizza.get_dietary_tags(),
            'farm': pizza.farm,
            'farm_story': pizza.farm_story,
            'latitude': float(pizza.latitude) if pizza.latitude else 36.348,
            'longitude': float(pizza.longitude) if pizza.longitude else 138.597,
            'image': pizza.image,
            'bestseller': pizza.bestseller,
            'seasonal_note': pizza.seasonal_note,
            'recommended_pairing': pizza.recommended_pairing,
            'recommended_pairing_price': pizza.recommended_pairing_price,
            'recommended_pairing_description': pizza.recommended_pairing_description,
            'recommended_pairing_image': pizza.recommended_pairing_image,
        })
    
    # Prepare sides data
    sides_data = []
    for item in sides:
        sides_data.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'image': item.image,
            'category': item.category,
        })
    
    # Prepare drinks data
    drinks_data = []
    for item in drinks:
        drinks_data.append({
            'id': item.id,
            'name': item.name,
            'description': item.description,
            'price': item.price,
            'image': item.image,
            'category': item.category,
        })
    
    context = {
        'pizzas': pizzas,
        'sides': sides,
        'drinks': drinks,
        'pizzas_json': json.dumps(pizzas_data),
        'sides_json': json.dumps(sides_data),
        'drinks_json': json.dumps(drinks_data),
    }
    
    # Cache for 1 hour
    cache.set(cache_key, context, 3600)
    
    return render(request, 'ember_rootapp/menu.html', context)


def story(request):
    """Story page view."""
    # Get total farm count for display
    pizzas = Pizza.objects.all()
    farms_set = set()
    for pizza in pizzas:
        if pizza.farm:
            farms_set.add(pizza.farm)
    total_farms = len(farms_set)
    
    context = {
        'total_farms': total_farms,
    }
    return render(request, 'ember_rootapp/story.html', context)


def distance(request):
    """Distance/Farms page view."""
    import json
    import math
    
    # Get ALL pizzas
    pizzas = Pizza.objects.all()
    
    print(f"DISTANCE VIEW: Found {pizzas.count()} pizzas")
    
    # Build farms dictionary
    farms_dict = {}
    for pizza in pizzas:
        farm_name = pizza.farm.strip() if pizza.farm else "Unknown Farm"
        if not farm_name:
            continue
        
        if farm_name not in farms_dict:
            # Calculate distance
            try:
                lat = float(pizza.latitude) if pizza.latitude else 36.348
                lng = float(pizza.longitude) if pizza.longitude else 138.597
                
                karuizawa_lat = 36.348
                karuizawa_lng = 138.597
                R = 6371
                dlat = math.radians(lat - karuizawa_lat)
                dlng = math.radians(lng - karuizawa_lng)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(karuizawa_lat)) * math.cos(math.radians(lat)) * math.sin(dlng/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance_km = int(R * c)
                distance_str = f"{distance_km}km"
            except:
                distance_str = "~45km"
            
            farms_dict[farm_name] = {
                'name': farm_name,
                'latitude': float(pizza.latitude) if pizza.latitude else 36.348,
                'longitude': float(pizza.longitude) if pizza.longitude else 138.597,
                'farm_story': pizza.farm_story or '',
                'pizzas': [],
                'icon': get_farm_icon(farm_name),
                'location': extract_location(farm_name),
                'distance': distance_str
            }
        
        if pizza.name not in farms_dict[farm_name]['pizzas']:
            farms_dict[farm_name]['pizzas'].append(pizza.name)
    
    farms = list(farms_dict.values())
    total_farms = len(farms)
    
    print(f"DISTANCE VIEW: {total_farms} unique farms found")
    print(f"DISTANCE VIEW: Farm names: {[f['name'] for f in farms]}")
    
    context = {
        'farms': farms,
        'total_farms': total_farms,
        'farms_json': json.dumps(farms),
        'farms_json_raw': json.dumps(farms),
    }
    return render(request, 'ember_rootapp/distance.html', context)


def get_farm_icon(farm_name):
    """Return appropriate icon based on farm name."""
    farm_lower = farm_name.lower()
    if 'dairy' in farm_lower or 'cheese' in farm_lower:
        return 'bi-cup-straw'
    elif 'pork' in farm_lower or 'meat' in farm_lower:
        return 'bi-egg-fried'
    elif 'mushroom' in farm_lower or 'forest' in farm_lower:
        return 'bi-flower1'
    elif 'apple' in farm_lower or 'orchard' in farm_lower:
        return 'bi-apple'
    elif 'wheat' in farm_lower or 'mill' in farm_lower or 'flour' in farm_lower:
        return 'bi-wheat'
    else:
        return 'bi-tree-fill'


def extract_location(farm_name):
    """Extract location from farm name."""
    parts = farm_name.split(',')
    if len(parts) > 1:
        return parts[1].strip()
    return 'Nagano Prefecture'


def calculate_distance_from_karuizawa(lat, lng):
    """Calculate distance from Karuizawa in km."""
    if not lat or not lng:
        return "~45km"
    
    import math
    karuizawa_lat = 36.348
    karuizawa_lng = 138.597
    
    R = 6371
    dlat = math.radians(float(lat) - karuizawa_lat)
    dlng = math.radians(float(lng) - karuizawa_lng)
    
    a = math.sin(dlat/2)**2 + math.cos(math.radians(karuizawa_lat)) * math.cos(math.radians(float(lat))) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return f"{int(distance)}km"

def privacy(request):
    """Privacy policy page."""
    return render(request, 'ember_rootapp/privacy.html')

def terms(request):
    """Terms of service page."""
    return render(request, 'ember_rootapp/terms.html')

def contact(request):
    """Contact page."""
    return render(request, 'ember_rootapp/contact.html')

def faq(request):
    """FAQ page."""
    return render(request, 'ember_rootapp/faq.html')

def get_business_hours():
    """Get formatted business hours for display."""
    hours = BusinessHours.objects.all().order_by('display_order')
    
    # Group consecutive days with same hours
    formatted = {}
    for h in hours:
        day_name = h.get_day_display()
        if h.is_closed:
            formatted[day_name] = {
                'status': 'closed',
                'note': h.note or 'Closed'
            }
        else:
            formatted[day_name] = {
                'status': 'open',
                'open': h.open_time.strftime('%H:%M') if h.open_time else '',
                'close': h.close_time.strftime('%H:%M') if h.close_time else '',
                'note': h.note or ''
            }
    return formatted

# the visit view
def visit(request):
    """Visit page view."""
    import datetime
    
    business_hours = BusinessHours.objects.all().order_by('display_order')
    
    # Get today's status
    today = datetime.datetime.now().strftime('%A').lower()
    today_hours = business_hours.filter(day=today).first()
    
    # Convert hours to JSON-safe format
    hours_list = []
    for h in business_hours:
        hours_list.append({
            'id': h.id,
            'day': h.day,
            'day_display': h.get_day_display(),
            'open_time': h.open_time.strftime('%H:%M') if h.open_time else '',
            'close_time': h.close_time.strftime('%H:%M') if h.close_time else '',
            'is_closed': h.is_closed,
            'note': h.note or '',
        })
    
    context = {
        'business_hours': business_hours,
        'today_hours': today_hours,
        'hours_json': json.dumps(hours_list), 
    }
    return render(request, 'ember_rootapp/visit.html', context)

# Admin API endpoints
@login_required
def admin_hours_list(request):
    """Get all business hours."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    hours = BusinessHours.objects.all().order_by('display_order')
    data = []
    for h in hours:
        data.append({
            'id': h.id,
            'day': h.day,
            'day_display': h.get_day_display(),
            'open_time': h.open_time.strftime('%H:%M') if h.open_time else '',
            'close_time': h.close_time.strftime('%H:%M') if h.close_time else '',
            'is_closed': h.is_closed,
            'note': h.note or '',
        })
    return JsonResponse({'hours': data})

@login_required
@require_POST
def admin_hours_update(request):
    """Update business hours."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    data = json.loads(request.body)
    hours_data = data.get('hours', [])
    
    for h in hours_data:
        BusinessHours.objects.update_or_create(
            day=h['day'],
            defaults={
                'open_time': h.get('open_time') or None,
                'close_time': h.get('close_time') or None,
                'is_closed': h.get('is_closed', False),
                'note': h.get('note', ''),
            }
        )
    
    return JsonResponse({'success': True, 'message': 'Business hours updated successfully'})

def api_business_hours(request):
    """API endpoint for business hours."""
    hours = BusinessHours.objects.all().order_by('display_order')
    data = {}
    for h in hours:
        day_name = h.get_day_display()
        if h.is_closed:
            data[day_name] = {
                'status': 'closed',
                'note': h.note or 'Closed'
            }
        else:
            data[day_name] = {
                'status': 'open',
                'open': h.open_time.strftime('%H:%M') if h.open_time else '',
                'close': h.close_time.strftime('%H:%M') if h.close_time else '',
                'note': h.note or ''
            }
    return JsonResponse({'hours': data})


# ==================== Cart & Orders ====================

@login_required
@require_POST
def place_order(request):
    """Place a new order."""
    user = request.user
    data = json.loads(request.body)
    
    cart_items = data.get('items', [])
    subtotal = data.get('subtotal', 0)
    total = data.get('total', 0)
    instructions = data.get('instructions', '')
    
    if not cart_items:
        return JsonResponse({
            'success': False,
            'message': 'Your cart is empty'
        })
    
    # Create order
    order = Order.objects.create(
        user=user,
        items=cart_items,
        subtotal=subtotal,
        total=total,
        special_instructions=instructions,
        status='confirmed'
    )
    
    log_user_activity(
        user,
        'order_placed',
        f'Order #{order.order_number} placed',
        request
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Order #{order.order_number} confirmed! Pickup in ~20 minutes.',
        'order_number': order.order_number
    })


@login_required
def order_history(request):
    """Get user's order history."""
    user = request.user
    status_filter = request.GET.get('status', 'all')
    
    orders = Order.objects.filter(user=user)
    if status_filter != 'all':
        orders = orders.filter(status=status_filter)
    
    orders = orders.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(orders, 10)
    page = request.GET.get('page', 1)
    orders_page = paginator.get_page(page)
    
    orders_data = []
    for order in orders_page:
        orders_data.append({
            'id': f'#ORD-{order.order_number.split("-")[-1]}',
            'order_number': order.order_number,
            'date': order.created_at.strftime('%B %d, %Y'),
            'items': ', '.join([item.get('name', '') for item in order.items]),
            'total': f'¥{order.total:,}',
            'status': order.status,
            'status_display': order.get_status_display(),
        })
    
    return JsonResponse({
        'success': True,
        'orders': orders_data,
        'has_next': orders_page.has_next(),
        'has_previous': orders_page.has_previous(),
        'total_pages': paginator.num_pages,
    })


# ==================== Favorites ====================

@login_required
@require_POST
def toggle_favorite(request, pizza_id):
    """Add or remove a pizza from favorites."""
    user = request.user
    pizza = get_object_or_404(Pizza, id=pizza_id, is_available=True)
    
    favorite, created = Favorite.objects.get_or_create(
        user=user,
        pizza=pizza
    )
    
    if not created:
        favorite.delete()
        log_user_activity(user, 'favorite_remove', f'Removed {pizza.name} from favorites', request)
        return JsonResponse({
            'success': True,
            'is_favorite': False,
            'message': f'Removed {pizza.name} from favorites'
        })
    
    log_user_activity(user, 'favorite_add', f'Added {pizza.name} to favorites', request)
    return JsonResponse({
        'success': True,
        'is_favorite': True,
        'message': f'Added {pizza.name} to favorites'
    })


@login_required
def get_favorites(request):
    """Get user's favorite pizzas."""
    user = request.user
    favorites = Favorite.objects.filter(
        user=user
    ).select_related('pizza').order_by('-created_at')
    
    favorites_data = []
    for fav in favorites:
        favorites_data.append({
            'id': fav.pizza.id,
            'name': fav.pizza.name,
            'price': fav.pizza.price,
            'image': fav.pizza.image,
            'description': fav.pizza.description,
            'calories': fav.pizza.calories,
            'farm': fav.pizza.farm,
            'dietary': fav.pizza.get_dietary_tags(),
            'category': fav.pizza.category,
        })
    
    return JsonResponse({
        'success': True,
        'favorites': favorites_data,
        'count': len(favorites_data)
    })


# ==================== Admin Views ====================

def is_admin(user):
    """Check if user is admin."""
    return user.is_authenticated and (user.is_admin_user or user.is_superuser)


# ==================== API Views ====================

def api_pizzas(request):
    """API endpoint for pizzas."""
    pizzas = Pizza.objects.filter(is_available=True)
    data = []
    for pizza in pizzas:
        data.append({
            'id': pizza.id,
            'name': pizza.name,
            'category': pizza.category,
            'description': pizza.description,
            'price': pizza.price,
            'calories': pizza.calories,
            'dietary': pizza.get_dietary_tags(),
            'farm': pizza.farm,
            'farm_story': pizza.farm_story,
            'latitude': pizza.latitude,
            'longitude': pizza.longitude,
            'image': pizza.image,
            'bestseller': pizza.bestseller,
            'seasonal_note': pizza.seasonal_note,
            'recommended_pairing': pizza.recommended_pairing,
            'recommended_pairing_price': pizza.recommended_pairing_price,
            'recommended_pairing_description': pizza.recommended_pairing_description,
            'recommended_pairing_image': pizza.recommended_pairing_image,
        })
    return JsonResponse({'pizzas': data})


def api_farm_stories(request):
    """API endpoint for farm stories."""
    pizzas = Pizza.objects.filter(is_available=True)
    stories = {}
    for pizza in pizzas:
        stories[pizza.name] = pizza.farm_story or f"{pizza.farm} is a family-owned farm within 120km of Karuizawa."
    return JsonResponse({'stories': stories})

def contact(request):
    """Contact page view."""
    form = ContactForm()
    
    context = {
        'form': form,
    }
    return render(request, 'ember_rootapp/contact.html', context)


@require_POST
def submit_contact(request):
    """Handle contact form submission via AJAX."""
    try:
        data = json.loads(request.body)
        
        form = ContactForm({
            'name': data.get('name', '').strip(),
            'email': data.get('email', '').strip().lower(),
            'subject': data.get('subject', 'general'),
            'message': data.get('message', '').strip(),
        })
        
        if form.is_valid():
            contact_message = form.save(commit=False)
            
            # Link to user if authenticated
            if request.user.is_authenticated:
                contact_message.user = request.user
            
            # Save IP and user agent
            contact_message.ip_address = get_client_ip(request)
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            contact_message.save()
            
            # Log activity if user is authenticated
            if request.user.is_authenticated:
                log_user_activity(
                    request.user,
                    'profile_update',
                    f'Submitted contact form: {contact_message.get_subject_display()}',
                    request
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Thank you, {contact_message.name}! We\'ll respond within 24 hours.',
            })
        else:
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = error_list[0]
            return JsonResponse({
                'success': False,
                'message': 'Please correct the errors below.',
                'errors': errors,
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data.',
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred. Please try again.',
        })
    
# ==================== Admin Dashboard API ====================

@login_required
def admin_dashboard(request):
    """Admin dashboard view."""
    if not is_admin(request.user):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    section = request.GET.get('section', 'dashboard')
    
    # Stats
    total_orders = Order.objects.count()
    total_revenue = Order.objects.filter(status='completed').aggregate(total=Sum('total'))['total'] or 0
    total_customers = User.objects.filter(user_type='customer').count()
    new_messages = ContactMessage.objects.filter(status='new').count()
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Recent messages
    recent_messages = ContactMessage.objects.order_by('-created_at')[:3]
    
    # Pizzas
    pizzas = Pizza.objects.all().order_by('category', 'name')
    
    # Sides and Drinks
    sides = MenuItem.objects.filter(category='sides').order_by('display_order', 'name')
    drinks = MenuItem.objects.filter(category='drinks').order_by('display_order', 'name')
    
    # All orders for orders tab
    all_orders = Order.objects.order_by('-created_at')[:20]
    
    # Customers - FIXED: Get all customers with user_type='customer'
    customers = User.objects.filter(user_type='customer').order_by('-created_at')[:20]
    
    # All messages for messages tab
    all_messages = ContactMessage.objects.order_by('-created_at')[:20]
    
    context = {
        'section': section,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_customers': total_customers,
        'new_messages': new_messages,
        'recent_orders': recent_orders,
        'recent_messages': recent_messages,
        'pizzas': pizzas,
        'sides': sides,
        'drinks': drinks,
        'all_orders': all_orders,
        'customers': customers,
        'all_messages': all_messages,
    }
    return render(request, 'ember_rootapp/admin/dashboard.html', context)


@login_required
@require_POST
def admin_pizza_create(request):
    """Create a new pizza from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    # Handle both JSON and FormData
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        image_file = None
        image_url = data.get('image', '')
        pairing_image_file = None
        pairing_image_url = data.get('pairing_image_url', '')
    else:
        data = request.POST
        image_file = request.FILES.get('image_file')
        image_url = data.get('image_url', '')
        pairing_image_file = request.FILES.get('pairing_image_file')
        pairing_image_url = data.get('pairing_image_url', '')
    
    # Handle pizza image
    image = image_url
    if image_file:
        file_path = default_storage.save(f'pizzas/{image_file.name}', ContentFile(image_file.read()))
        image = default_storage.url(file_path)

    # Handle pairing image
    pairing_image = pairing_image_url
    if pairing_image_file:
        file_path = default_storage.save(f'pizzas/pairings/{pairing_image_file.name}', ContentFile(pairing_image_file.read()))
        pairing_image = default_storage.url(file_path)
    
    # Parse dietary if it's a string
    dietary = data.get('dietary', [])
    if isinstance(dietary, str):
        try:
            dietary = json.loads(dietary)
        except:
            dietary = [d.strip() for d in dietary.split(',') if d.strip()]
    
    pizza = Pizza.objects.create(
        name=data.get('name'),
        category=data.get('category', 'classics'),
        description=data.get('description', ''),
        price=int(data.get('price', 0)),
        calories=int(data.get('calories', 0)),
        dietary=dietary,
        bestseller=data.get('bestseller', 'false').lower() in ['true', 'on', '1'],
        seasonal_note=data.get('seasonal_note', ''),
        farm=data.get('farm', ''),
        latitude=float(data.get('latitude', 36.348)),
        longitude=float(data.get('longitude', 138.597)),
        farm_story=data.get('farm_story', ''),
        image=image,
        recommended_pairing=data.get('recommended_pairing', ''),
        recommended_pairing_price=int(data.get('recommended_pairing_price', 0)) if data.get('recommended_pairing_price') else None,
        recommended_pairing_description=data.get('recommended_pairing_description', ''),
        recommended_pairing_image=pairing_image,
        created_by=request.user
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Pizza "{pizza.name}" created successfully!',
        'pizza': {'id': pizza.id, 'name': pizza.name}
    })


@login_required
@require_POST
def admin_pizza_update(request, pizza_id):
    """Update a pizza from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    pizza = get_object_or_404(Pizza, id=pizza_id)
    
    # Store old image paths for cleanup (but DON'T delete yet!)
    old_pizza_image = pizza.image
    old_pairing_image = pizza.recommended_pairing_image
    
    # Handle both JSON and FormData
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        image_file = None
        image_url = data.get('image', '')
        pairing_image_file = None
        pairing_image_url = data.get('pairing_image_url', '')
    else:
        data = request.POST
        image_file = request.FILES.get('image_file')
        image_url = data.get('image_url', '')
        pairing_image_file = request.FILES.get('pairing_image_file')
        pairing_image_url = data.get('pairing_image_url', '')
    
    # Update fields
    pizza.name = data.get('name', pizza.name)
    pizza.category = data.get('category', pizza.category)
    pizza.description = data.get('description', pizza.description)
    pizza.price = int(data.get('price', pizza.price))
    pizza.calories = int(data.get('calories', pizza.calories))
    
    # Parse dietary
    dietary = data.get('dietary', pizza.dietary)
    if isinstance(dietary, str):
        try:
            dietary = json.loads(dietary)
        except:
            dietary = [d.strip() for d in dietary.split(',') if d.strip()]
    pizza.dietary = dietary
    
    pizza.bestseller = data.get('bestseller', 'false').lower() in ['true', 'on', '1']
    pizza.seasonal_note = data.get('seasonal_note', pizza.seasonal_note)
    pizza.farm = data.get('farm', pizza.farm)
    pizza.latitude = float(data.get('latitude', pizza.latitude))
    pizza.longitude = float(data.get('longitude', pizza.longitude))
    pizza.farm_story = data.get('farm_story', pizza.farm_story)
    
    # Track if image was updated
    image_updated = False
    pairing_image_updated = False
    
    # Handle pizza image
    if image_file:
        # Delete old image if it exists and is a local file
        if old_pizza_image and old_pizza_image.startswith('/media/'):
            delete_media_file(old_pizza_image)
        
        # Save new image
        file_path = default_storage.save(f'pizzas/{image_file.name}', ContentFile(image_file.read()))
        pizza.image = default_storage.url(file_path)
        image_updated = True
    elif image_url and image_url != old_pizza_image:
        # Delete old image if it exists and is a local file
        if old_pizza_image and old_pizza_image.startswith('/media/'):
            delete_media_file(old_pizza_image)
        pizza.image = image_url
        image_updated = True
    
    # Handle pairing image
    if pairing_image_file:
        # Delete old pairing image if it exists and is a local file
        if old_pairing_image and old_pairing_image.startswith('/media/'):
            delete_media_file(old_pairing_image)
        
        # Save new pairing image
        file_path = default_storage.save(f'pizzas/pairings/{pairing_image_file.name}', ContentFile(pairing_image_file.read()))
        pizza.recommended_pairing_image = default_storage.url(file_path)
        pairing_image_updated = True
    elif pairing_image_url and pairing_image_url != old_pairing_image:
        # Delete old pairing image if it exists and is a local file
        if old_pairing_image and old_pairing_image.startswith('/media/'):
            delete_media_file(old_pairing_image)
        pizza.recommended_pairing_image = pairing_image_url
        pairing_image_updated = True
    
    pizza.recommended_pairing = data.get('recommended_pairing', pizza.recommended_pairing)
    pizza.recommended_pairing_price = int(data.get('recommended_pairing_price', 0)) if data.get('recommended_pairing_price') else None
    pizza.recommended_pairing_description = data.get('recommended_pairing_description', pizza.recommended_pairing_description)
    
    pizza.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Pizza "{pizza.name}" updated successfully!',
        'pizza': {
            'id': pizza.id, 
            'name': pizza.name,
            'image': pizza.image,
            'recommended_pairing_image': pizza.recommended_pairing_image
        }
    })


@login_required
@require_POST
def admin_pizza_delete(request, pizza_id):
    """Delete a pizza from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    pizza = get_object_or_404(Pizza, id=pizza_id)
    pizza_name = pizza.name
    
    # Delete associated image files (don't let file errors prevent pizza deletion)
    try:
        delete_media_file(pizza.image)
        delete_media_file(pizza.recommended_pairing_image)
    except Exception as e:
        # Log the error but continue with pizza deletion
        print(f"Error deleting media files for pizza {pizza_id}: {e}")
    
    # Delete the pizza from database
    pizza.delete()
    
    return JsonResponse({
        'success': True, 
        'message': f'Pizza "{pizza_name}" deleted successfully'
    })


@login_required
@require_POST
def admin_menuitem_create(request):
    """Create a new menu item from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    # Handle both JSON and FormData
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        image_file = None
        image_url = data.get('image', '')
    else:
        data = request.POST
        image_file = request.FILES.get('image_file')
        image_url = data.get('image_url', '')
    
    # Handle image
    image = image_url
    if image_file:
        file_path = default_storage.save(f'menu_items/{image_file.name}', ContentFile(image_file.read()))
        image = default_storage.url(file_path)
    
    item = MenuItem.objects.create(
        name=data.get('name'),
        category=data.get('category', 'sides'),
        description=data.get('description', ''),
        price=int(data.get('price', 0)),
        image=image,
        is_available=data.get('is_available', 'true') in ['true', True, 'on', '1']
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Menu item "{item.name}" created successfully!',
        'item': {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'description': item.description,
            'price': item.price,
            'image': item.image,
            'is_available': item.is_available,
        }
    })


@login_required
@require_POST
def admin_menuitem_update(request, item_id):
    """Update a menu item from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    item = get_object_or_404(MenuItem, id=item_id)
    
    # Handle both JSON and FormData
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        image_file = None
        image_url = data.get('image', '')
    else:
        data = request.POST
        image_file = request.FILES.get('image_file')
        image_url = data.get('image_url', '')
    
    item.name = data.get('name', item.name)
    item.category = data.get('category', item.category)
    item.description = data.get('description', item.description)
    item.price = int(data.get('price', item.price))
    item.is_available = data.get('is_available', 'true') in ['true', True, 'on', '1']
    
    # Handle image
    if image_file:
        if item.image and item.image.startswith('/media/'):
            delete_media_file(item.image)
        file_path = default_storage.save(f'menu_items/{image_file.name}', ContentFile(image_file.read()))
        item.image = default_storage.url(file_path)
    elif image_url:
        item.image = image_url
    
    item.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Menu item "{item.name}" updated successfully!',
        'item': {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'description': item.description,
            'price': item.price,
            'image': item.image,
            'is_available': item.is_available,
        }
    })


@login_required
@require_POST
def admin_menuitem_delete(request, item_id):
    """Delete a menu item from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    return JsonResponse({'success': True, 'message': 'Menu item deleted successfully'})


@login_required
@require_POST
def admin_order_status(request, order_id):
    """Update order status from admin dashboard."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    order = get_object_or_404(Order, id=order_id)
    data = json.loads(request.body)
    order.status = data.get('status', order.status)
    order.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Order {order.order_number} status updated',
        'status_display': order.get_status_display()
    })

@login_required
def admin_pizza_detail(request, pizza_id):
    """Get pizza details for editing."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    pizza = get_object_or_404(Pizza, id=pizza_id)
    return JsonResponse({
        'id': pizza.id,
        'name': pizza.name,
        'category': pizza.category,
        'description': pizza.description,
        'price': pizza.price,
        'calories': pizza.calories,
        'farm': pizza.farm,
        'dietary': pizza.get_dietary_tags(),
        'bestseller': pizza.bestseller,
        'is_available': pizza.is_available,
        'image': pizza.image,
        'seasonal_note': pizza.seasonal_note,
        'latitude': float(pizza.latitude),
        'longitude': float(pizza.longitude),
        'farm_story': pizza.farm_story or '',
        'recommended_pairing': pizza.recommended_pairing or '',
        'recommended_pairing_price': pizza.recommended_pairing_price or '',
        'recommended_pairing_description': pizza.recommended_pairing_description or '',
        'recommended_pairing_image': pizza.recommended_pairing_image or '',
    })

@login_required
def admin_menuitem_detail(request, item_id):
    """Get menu item details for editing."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    item = get_object_or_404(MenuItem, id=item_id)
    return JsonResponse({
        'id': item.id,
        'name': item.name,
        'category': item.category,
        'description': item.description,
        'price': item.price,
        'image': item.image,
        'is_available': item.is_available,
    })


@login_required
def admin_message_detail(request, message_id):
    """Get message details for viewing."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    msg = get_object_or_404(ContactMessage, id=message_id)
    return JsonResponse({
        'id': msg.id,
        'name': msg.name,
        'email': msg.email,
        'subject': msg.subject,
        'subject_display': msg.get_subject_display(),
        'message': msg.message,
        'status': msg.status,
        'status_display': msg.get_status_display(),
        'date': msg.created_at.strftime('%Y-%m-%d %H:%M'),
    })

@login_required
def admin_profile(request):
    """Get admin profile data."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    return JsonResponse({
        'name': request.user.get_full_name() or request.user.first_name or request.user.email,
        'email': request.user.email,
        'phone': request.user.phone or '',
    })


@login_required
@require_POST
def admin_profile_update(request):
    """Update admin profile."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    data = json.loads(request.body)
    user = request.user
    
    # Verify current password
    current_password = data.get('current_password', '')
    if not user.check_password(current_password):
        return JsonResponse({'success': False, 'message': 'Current password is incorrect'})
    
    # Update name
    name = data.get('name', '').strip()
    if name:
        parts = name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
    
    # Update email
    email = data.get('email', '').strip().lower()
    if email and email != user.email:
        if User.objects.filter(email=email).exclude(id=user.id).exists():
            return JsonResponse({'success': False, 'message': 'Email already in use'})
        user.email = email
        user.username = email
    
    # Update phone
    phone = data.get('phone', '').strip()
    if phone:
        user.phone = phone
    
    # Update password if provided
    new_password = data.get('new_password', '')
    if new_password:
        user.set_password(new_password)
    
    user.save()
    
    log_user_activity(user, 'profile_update', 'Updated admin profile', request)
    
    return JsonResponse({'success': True, 'message': 'Profile updated successfully'})

@login_required
@require_POST
def admin_message_reply(request, message_id):
    """Send a reply to a contact message."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    data = json.loads(request.body)
    reply_text = data.get('reply', '').strip()
    
    if not reply_text:
        return JsonResponse({'success': False, 'message': 'Reply cannot be empty'})
    
    msg = get_object_or_404(ContactMessage, id=message_id)
    
    # Save reply
    msg.reply = reply_text
    msg.replied_by = request.user
    msg.replied_at = timezone.now()
    msg.status = 'replied'
    msg.save()
    
    log_user_activity(
        request.user,
        'profile_update',
        f'Replied to message from {msg.name}',
        request
    )
    
    return JsonResponse({
        'success': True,
        'message': 'Reply sent successfully'
    })

@login_required
@require_POST
def mark_messages_as_read(request):
    """Mark all user's replied messages as read."""
    user = request.user
    
    # Update all unread replied messages for this user
    updated = ContactMessage.objects.filter(
        Q(user=user) | Q(email=user.email)
    ).exclude(
        reply__isnull=True
    ).exclude(
        reply=''
    ).filter(
        read_by_user=False
    ).update(read_by_user=True)
    
    return JsonResponse({
        'success': True,
        'marked_read': updated
    })

@login_required
def admin_order_detail(request, order_id):
    """Get order details with items."""
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Access denied'})
    
    order = get_object_or_404(Order, id=order_id)
    return JsonResponse({
        'id': order.id,
        'order_number': order.order_number,
        'items': order.items,  # This is the JSON field with qty, name, price
        'total': order.total,
        'status': order.status,
        'status_display': order.get_status_display(),
        'date': order.created_at.strftime('%Y-%m-%d %H:%M'),
        'customer': order.user.get_full_name() or order.user.email,
        'instructions': order.special_instructions or '',
    })

def get_stats(request):
    """API endpoint for getting site statistics with caching."""
    from .models import Pizza
    
    # Check cache first (cache for 1 hour = 3600 seconds)
    cache_key = 'site_stats'
    stats = cache.get(cache_key)
    
    if stats is None:
        # Count unique farm names from Pizza model
        unique_farms = set()
        pizzas = Pizza.objects.filter(is_available=True)
        for pizza in pizzas:
            if pizza.farm:
                unique_farms.add(pizza.farm.strip())
        
        farm_count = len(unique_farms)
        pizza_count = Pizza.objects.filter(is_available=True).count()
        
        # FAQ counts - could be made dynamic if you store FAQs in database
        # For now, these are based on your template structure
        faq_count = 24  # Total FAQ items in template
        category_count = 6  # Number of categories
        
        stats = {
            'farm_count': farm_count,
            'pizza_count': pizza_count,
            'faq_count': faq_count,
            'category_count': category_count,
        }
        
        # Cache for 1 hour
        cache.set(cache_key, stats, 3600)
    
    return JsonResponse(stats)