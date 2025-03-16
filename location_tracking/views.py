from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from .models import LocationData
import json
from django.db import models

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def map_view(request):
    # Get users with active locations, ordered by last timestamp
    users_with_locations = User.objects.filter(
        locations__is_active=True
    ).annotate(
        latest_timestamp=models.Max('locations__timestamp')
    ).order_by('-latest_timestamp').distinct()
    
    # Group users by batch if education data is available
    batch_groups = {}
    for user in users_with_locations:
        try:
            # Get primary education for batch info
            education = user.profile.education.filter(is_primary=True).first()
            batch = education.graduation_year if education else "Unknown"
            
            # Get the latest location data for this user
            latest_location = LocationData.objects.filter(
                user=user, 
                is_active=True
            ).order_by('-timestamp').first()
            
            latitude = float(latest_location.latitude) if latest_location else None
            longitude = float(latest_location.longitude) if latest_location else None
            
            if batch not in batch_groups:
                batch_groups[batch] = []
            
            batch_groups[batch].append({
                'name': user.get_full_name() or user.username,
                'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None,
                'course': education.get_program_display() if education else "Unknown",
                'latitude': latitude,
                'longitude': longitude
            })
        except Exception as e:
            # Handle users without profile or education
            if "Unknown" not in batch_groups:
                batch_groups["Unknown"] = []
            
            # Get the latest location data for this user
            try:
                latest_location = LocationData.objects.filter(
                    user=user, 
                    is_active=True
                ).order_by('-timestamp').first()
                
                latitude = float(latest_location.latitude) if latest_location else None
                longitude = float(latest_location.longitude) if latest_location else None
            except:
                latitude = None
                longitude = None
            
            batch_groups["Unknown"].append({
                'name': user.get_full_name() or user.username,
                'avatar': None,
                'course': "Unknown",
                'latitude': latitude,
                'longitude': longitude
            })
    
    # Sort batch groups by year (newest first)
    sorted_batch_groups = dict(sorted(batch_groups.items(), key=lambda x: (x[0] != "Unknown", x[0]), reverse=True))
    
    context = {
        'users': users_with_locations,
        'batch_groups': sorted_batch_groups,
        'total_users': users_with_locations.count(),
    }
    return render(request, 'location_tracking/map.html', context)

@csrf_exempt
def update_location(request):
    """Update or create location data for the authenticated user."""
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            # Parse JSON data - handle different content types for better mobile support
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                # Fallback for different content types
                data = request.POST
                if not data:
                    # If still empty, try parsing the body
                    try:
                        data = json.loads(request.body)
                    except:
                        data = {}
            
            lat = data.get('latitude')
            lng = data.get('longitude')
            
            # Validate coordinates
            if not lat or not lng:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing latitude or longitude'
                }, status=400)
            
            try:
                lat = float(lat)
                lng = float(lng)
                
                # Basic validation of coordinates
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid coordinates'
                    }, status=400)
            except (ValueError, TypeError):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coordinates must be valid numbers'
                }, status=400)
            
            # Update or create location data
            location, created = LocationData.objects.update_or_create(
                user=request.user,
                defaults={
                    'latitude': lat,
                    'longitude': lng,
                    'is_active': True
                }
            )
            
            action = 'created' if created else 'updated'
            return JsonResponse({
                'status': 'success',
                'message': f'Location {action} successfully',
                'location': {
                    'latitude': float(location.latitude),
                    'longitude': float(location.longitude),
                    'timestamp': location.timestamp.isoformat(),
                    'is_active': location.is_active
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            # Log the exception for debugging
            import logging
            logging.error(f"Location update error: {str(e)}")
            
            return JsonResponse({
                'status': 'error',
                'message': f'An error occurred: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request or user not authenticated'
    }, status=401)

@user_passes_test(is_admin)
def get_all_locations(request):
    locations = LocationData.objects.filter(is_active=True).select_related(
        'user',
        'user__profile'
    ).prefetch_related(
        'user__profile__education'
    )
    
    data = []
    for location in locations:
        # Get primary education record
        education = location.user.profile.education.filter(is_primary=True).first()
        
        data.append({
            'user': location.user.get_full_name() or location.user.username,
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'timestamp': location.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'avatar': location.user.profile.avatar.url if hasattr(location.user, 'profile') and location.user.profile.avatar else None,
            'batch': education.graduation_year if education else None,
            'course': education.get_program_display() if education else None,
            'location': location.user.profile.city if hasattr(location.user, 'profile') else None,
        })
    return JsonResponse({'locations': data})
