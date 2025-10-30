"""
Subresource Integrity (SRI) utilities for generating and managing SRI hashes
"""
import hashlib
import base64
import os
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


def generate_sri_hash(file_path, algorithm='sha384'):
    """
    Generate SRI hash for a given file
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (sha256, sha384, sha512)
    
    Returns:
        SRI hash string in format: algorithm-base64hash
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Create hash
        if algorithm == 'sha256':
            hash_obj = hashlib.sha256(content)
        elif algorithm == 'sha384':
            hash_obj = hashlib.sha384(content)
        elif algorithm == 'sha512':
            hash_obj = hashlib.sha512(content)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Encode to base64
        hash_b64 = base64.b64encode(hash_obj.digest()).decode('utf-8')
        
        return f"{algorithm}-{hash_b64}"
    
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error generating SRI hash for {file_path}: {e}")
        return None


def _hash_for_static(asset_path: str, algorithm: str = 'sha384'):
    """Resolve a logical static path to its stored file and compute SRI.

    Works with ManifestStaticFilesStorage/Whitenoise where filenames are hashed.
    """
    try:
        real_path = staticfiles_storage.path(asset_path)
    except Exception:
        # Fallback to STATIC/STATIC_ROOT manual resolution
        static_root = getattr(settings, 'STATICFILES_DIRS', [])
        base = static_root[0] if static_root else os.path.join(settings.BASE_DIR, 'static')
        real_path = os.path.join(base, asset_path.replace('/', os.sep))
    return generate_sri_hash(real_path, algorithm)


def get_leaflet_sri_hashes():
    """
    Get SRI hashes for all self-hosted Leaflet files
    
    Returns:
        Dictionary with file names as keys and SRI hashes as values
    """
    assets = {
        'leaflet.css': 'css/leaflet/leaflet.css',
        'MarkerCluster.css': 'css/leaflet/MarkerCluster.css',
        'MarkerCluster.Default.css': 'css/leaflet/MarkerCluster.Default.css',
        'leaflet.js': 'js/leaflet/leaflet.js',
        'leaflet.markercluster.js': 'js/leaflet/leaflet.markercluster.js',
    }

    sri_hashes = {}
    for key, logical_path in assets.items():
        sri_hash = _hash_for_static(logical_path)
        if sri_hash:
            sri_hashes[key] = sri_hash

    return sri_hashes


# Generate SRI hashes at import time using the actual stored files
def _initial_leaflet_sri_hashes():
    hashes = get_leaflet_sri_hashes()
    # Map keys to template-friendly names used in context
    return {
        'leaflet_css': hashes.get('leaflet.css'),
        'MarkerCluster_css': hashes.get('MarkerCluster.css'),
        'MarkerCluster_Default_css': hashes.get('MarkerCluster.Default.css'),
        'leaflet_js': hashes.get('leaflet.js'),
        'leaflet_markercluster_js': hashes.get('leaflet.markercluster.js'),
    }

LEAFLET_SRI_HASHES = _initial_leaflet_sri_hashes()

# Function to update SRI hashes
def update_sri_hashes():
    """Update the SRI hashes for all Leaflet files"""
    global LEAFLET_SRI_HASHES
    LEAFLET_SRI_HASHES = _initial_leaflet_sri_hashes()
    return LEAFLET_SRI_HASHES