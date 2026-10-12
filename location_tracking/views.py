"""Staff-only alumni map and opt-in location endpoint.

A recorded position is a last-shared position, never proof of current presence.
"""
import json
import logging
import math
from datetime import timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from alumni_directory.models import Alumni
from .models import LocationData

logger = logging.getLogger(__name__)
MAP_LOOKBACK_DAYS = 90
GEOCODER_CACHE_SECONDS = 7 * 24 * 3600


def is_admin(user):
    if not user.is_authenticated:
        return False
    profile = getattr(user, 'profile', None)
    return bool(user.is_superuser or user.is_staff or (profile and profile.is_alumni_coordinator))


def _latest_verified_locations():
    """One latest, active position per verified alumnus, never non-alumni staff."""
    cutoff = timezone.now() - timedelta(days=MAP_LOOKBACK_DAYS)
    queryset = (LocationData.objects.filter(
        is_active=True, timestamp__gte=cutoff, user__alumni__is_verified=True,
    ).select_related('user', 'user__alumni', 'user__profile').order_by('-timestamp', '-pk'))
    seen = set()
    results = []
    for position in queryset:
        if position.user_id in seen:
            continue
        seen.add(position.user_id)
        alumni = position.user.alumni
        profile = getattr(position.user, 'profile', None)
        try:
            avatar_url = profile.avatar.url if profile and profile.avatar else None
        except (ValueError, OSError):
            avatar_url = None
        results.append({
            'id': position.user_id,
            'position_id': position.pk,
            'user': position.user.get_full_name() or position.user.username,
            'batch': str(alumni.graduation_year) if alumni.graduation_year else 'Unknown',
            'course': alumni.course or 'Unknown program',
            'location': (profile.city if profile and profile.city else alumni.city) or 'Unknown city',
            'latitude': float(position.latitude),
            'longitude': float(position.longitude),
            'timestamp': position.timestamp.isoformat(),
            'avatar': avatar_url,
        })
    return results


@user_passes_test(is_admin)
@never_cache
def map_view(request):
    """Render a light shell; locations come from the permission-checked JSON endpoint."""
    return render(request, 'location_tracking/map.html', {
        # These are browser-side service keys, NOT Django SECRET_KEY or credentials.
        # Restrict permitted websites in the respective tile-service dashboard.
        'carto_basemap_key': getattr(settings, 'LOCATION_CARTO_BASEMAP_KEY', ''),
        'maptiler_basemap_key': getattr(settings, 'LOCATION_MAPTILER_BASEMAP_KEY', ''),
    })


@require_GET
@user_passes_test(is_admin)
@never_cache
def get_all_locations(request):
    return JsonResponse({'locations': _latest_verified_locations(), 'lookback_days': MAP_LOOKBACK_DAYS})


@require_GET
@login_required
@never_cache
def sharing_status(request):
    """Return the signed-in alumnus's persisted map status, not browser permission."""
    eligible = Alumni.objects.filter(user_id=request.user.pk, is_verified=True).exists()
    location = None
    if eligible:
        location = (LocationData.objects.filter(
            user=request.user, is_active=True,
            timestamp__gte=timezone.now() - timedelta(days=MAP_LOOKBACK_DAYS),
        ).order_by('-timestamp', '-pk').first())
    return JsonResponse({
        'eligible': eligible,
        'has_active_location': location is not None,
        'last_shared_at': location.timestamp.isoformat() if location else None,
    })


@require_POST
@login_required
@never_cache
def update_location(request):
    """Only a verified alumnus can share their own coordinates (CSRF protected)."""
    if not Alumni.objects.filter(user_id=request.user.pk, is_verified=True).exists():
        return JsonResponse({'status': 'error', 'message': 'Verified alumni access required.'}, status=403)
    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
        else:
            payload = request.POST
        latitude, longitude = float(payload['latitude']), float(payload['longitude'])
        if not (math.isfinite(latitude) and math.isfinite(longitude)
                and -90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError('Out-of-range coordinates')
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Valid latitude and longitude are required.'}, status=400)
    # Retain a single active position per user, preserving the existing history behavior.
    from django.db import transaction
    with transaction.atomic():
        LocationData.objects.filter(user=request.user, is_active=True).update(is_active=False)
        location = LocationData.objects.create(
            user=request.user, latitude=latitude, longitude=longitude, is_active=True,
        )
    return JsonResponse({
        'status': 'success', 'success': True, 'message': 'Location shared successfully.',
        'location': {'latitude': float(location.latitude), 'longitude': float(location.longitude),
                     'timestamp': location.timestamp.isoformat(), 'is_active': True},
    })


@require_POST
@login_required
@never_cache
def stop_sharing_location(request):
    """Remove all active map positions when an account withdraws consent."""
    LocationData.objects.filter(user=request.user, is_active=True).update(is_active=False)
    return JsonResponse({'status': 'success', 'success': True, 'message': 'Location sharing stopped.'})


@require_POST
@user_passes_test(is_admin)
@never_cache
def lookup_street_address(request, position_id):
    """On-demand reverse geocoding, never a bulk request for all map pins.

    Precise coordinates are sent to Nominatim ONLY after an admin explicitly clicks
    'Look up address'. Deploy with a shared Django cache for global request throttling.
    """
    position = (LocationData.objects.filter(
        pk=position_id, is_active=True,
        timestamp__gte=timezone.now() - timedelta(days=MAP_LOOKBACK_DAYS),
        user__alumni__is_verified=True,
    ).first())
    if not position:
        return JsonResponse({'message': 'This shared location is no longer available.'}, status=404)

    contact = getattr(settings, 'LOCATION_GEOCODER_CONTACT_EMAIL', '') or ''
    if not contact or '@' not in contact:
        return JsonResponse({'message': 'Address lookup is not configured. Set LOCATION_GEOCODER_CONTACT_EMAIL.'}, status=503)

    lat, lon = float(position.latitude), float(position.longitude)
    key = f'location:reverse:v1:{lat:.5f}:{lon:.5f}'
    cached = cache.get(key)
    if cached is not None:
        return JsonResponse(cached)
    # The shared cache prevents concurrent requests from exceeding the public
    # Nominatim service's hard 1 request/second limit. No automatic retries.
    if not cache.add('location:nominatim:request_lock', '1', timeout=2):
        return JsonResponse({'message': 'Address lookup is busy. Try again in a few seconds.'}, status=429)

    params = urlencode({'format': 'jsonv2', 'lat': f'{lat:.6f}', 'lon': f'{lon:.6f}',
                        'zoom': 18, 'addressdetails': 1})
    request_url = f'https://nominatim.openstreetmap.org/reverse?{params}'
    req = Request(request_url, headers={
        'User-Agent': f'NORSUAlumniMap/1.0 (contact: {contact})',
        'Accept': 'application/json',
    })
    try:
        with urlopen(req, timeout=5) as response:
            result = json.loads(response.read(32768))
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
        logger.warning('Reverse geocoder unavailable: %s', type(exc).__name__)
        return JsonResponse({'message': 'Address service unavailable. Please try again later.'}, status=502)

    address = result.get('address') or {}
    road = address.get('road') or address.get('pedestrian') or address.get('residential')
    number = address.get('house_number')
    city = (address.get('city') or address.get('town') or address.get('municipality')
            or address.get('village') or address.get('county'))
    detail = ', '.join(filter(None, [f'{number} {road}' if road and number else road,
                                   address.get('suburb') or address.get('neighbourhood'),
                                   city, address.get('state')]))
    payload = {
        'address': detail or result.get('display_name') or 'No mapped address found',
        'precision': 'street' if road else 'area',
        'note': ('Mapped street estimate; not a verified residential address.' if road else
                 'Only the approximate mapped area is available.'),
        'attribution': '© OpenStreetMap contributors (Nominatim)',
    }
    cache.set(key, payload, GEOCODER_CACHE_SECONDS)
    return JsonResponse(payload)
