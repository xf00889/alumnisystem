"""
Subresource Integrity (SRI) utilities for generating and managing SRI hashes
"""
import hashlib
import base64
import os
from django.conf import settings


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


def get_leaflet_sri_hashes():
    """
    Get SRI hashes for all self-hosted Leaflet files
    
    Returns:
        Dictionary with file names as keys and SRI hashes as values
    """
    static_root = getattr(settings, 'STATICFILES_DIRS', [])
    if static_root:
        static_path = static_root[0]
    else:
        static_path = os.path.join(settings.BASE_DIR, 'static')
    
    leaflet_files = {
        'leaflet.css': os.path.join(static_path, 'css', 'leaflet', 'leaflet.css'),
        'MarkerCluster.css': os.path.join(static_path, 'css', 'leaflet', 'MarkerCluster.css'),
        'MarkerCluster.Default.css': os.path.join(static_path, 'css', 'leaflet', 'MarkerCluster.Default.css'),
        'leaflet.js': os.path.join(static_path, 'js', 'leaflet', 'leaflet.js'),
        'leaflet.markercluster.js': os.path.join(static_path, 'js', 'leaflet', 'leaflet.markercluster.js'),
    }
    
    sri_hashes = {}
    for file_name, file_path in leaflet_files.items():
        sri_hash = generate_sri_hash(file_path)
        if sri_hash:
            sri_hashes[file_name] = sri_hash
    
    return sri_hashes


# Pre-generate SRI hashes (these will be updated when files change)
LEAFLET_SRI_HASHES = {
    'leaflet_css': 'sha384-a1Ehh0uaSKXoYj3VdLeT14oR26DDhFiU6/uhWGOrIiAHLSmsfaJ92hWSyD5GNWWt',
    'MarkerCluster_css': 'sha384-O6v6N8WWfJqWJZA3Vz39Y+Smwmv5PRYET+VyrLHv2oSbwM5tj7Z8tpmxbxwa+mxN',
    'MarkerCluster_Default_css': 'sha384-wgw+aLYNQ7dlhK47ZPK7FRACiq7ROZwgFNg0m04avm4CaXS+Z9Y7nMu8yNjBKYC+',
    'leaflet_js': 'sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH',
    'leaflet_markercluster_js': 'sha384-Pia3L1tpt6rSjrM5hA7rqsy5t9w7ZHwMY+4/9B6aqqcNNqr8eBuA7C8Z1X9YR7tK',
}

# Function to update SRI hashes
def update_sri_hashes():
    """Update the SRI hashes for all Leaflet files"""
    global LEAFLET_SRI_HASHES
    LEAFLET_SRI_HASHES.update(get_leaflet_sri_hashes())
    return LEAFLET_SRI_HASHES