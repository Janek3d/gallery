"""
Utility functions for Gallery app, including signed URL generation for SeaweedFS
"""
import hmac
import hashlib
import base64
import time
from urllib.parse import urlencode, quote
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def generate_signed_url(file_id, expires_in=3600, secret_key=None, algorithm='md5'):
    """
    Generate a signed URL for SeaweedFS file access.
    
    The signed URL format is compatible with Nginx secure_link module:
    /path/to/file?st=signature&e=expires
    
    Args:
        file_id: SeaweedFS file ID
        expires_in: URL expiration time in seconds (default: 1 hour)
        secret_key: Secret key for signing (defaults to SECRET_KEY from settings)
        algorithm: Hash algorithm ('md5' for nginx secure_link, 'sha256' for custom)
    
    Returns:
        dict with 'url' and 'expires_at' keys
    """
    if secret_key is None:
        secret_key = getattr(settings, 'GALLERY_SIGNED_URL_SECRET', None)
        if secret_key is None:
            # Fallback to Django SECRET_KEY
            secret_key = settings.SECRET_KEY
    
    if not secret_key:
        raise ImproperlyConfigured(
            "GALLERY_SIGNED_URL_SECRET or SECRET_KEY must be set for signed URLs"
        )
    
    # Calculate expiration timestamp
    expires_at = int(time.time()) + expires_in
    
    # Get base URL and construct full URI path
    base_url = getattr(settings, 'GALLERY_MEDIA_BASE_URL', '/media')
    uri_path = f"{base_url}/{quote(file_id)}"
    
    # Create the string to sign
    # For nginx secure_link_md5: "$uri$secure_link_expires$secure_link_secret"
    # This means: /media/file_id + expires_at + secret_key
    string_to_sign = f"{uri_path}{expires_at}{secret_key}"
    
    # Generate signature based on algorithm
    if algorithm == 'md5':
        # Use MD5 for nginx secure_link compatibility
        signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest()
    else:
        # Use HMAC-SHA256 for custom validation
        signature = hmac.new(
            secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        signature = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    # Build query parameters
    params = {
        'st': signature,      # signature
        'e': expires_at       # expires
    }
    
    # Construct the signed URL
    signed_url = f"{uri_path}?{urlencode(params)}"
    
    return {
        'url': signed_url,
        'expires_at': expires_at,
        'expires_in': expires_in
    }


def verify_signed_url(file_id, signature, expires_at, secret_key=None, algorithm='md5', uri_path=None):
    """
    Verify a signed URL signature.
    
    This can be used server-side for additional validation (Nginx handles it by default).
    
    Args:
        file_id: SeaweedFS file ID
        signature: Signature from URL (st parameter)
        expires_at: Expiration timestamp from URL (e parameter)
        secret_key: Secret key for verification
        algorithm: Hash algorithm ('md5' or 'sha256')
        uri_path: Full URI path (for MD5 verification)
    
    Returns:
        bool: True if signature is valid and not expired
    """
    if secret_key is None:
        secret_key = getattr(settings, 'GALLERY_SIGNED_URL_SECRET', None)
        if secret_key is None:
            secret_key = settings.SECRET_KEY
    
    if not secret_key:
        return False
    
    # Check if expired
    if int(time.time()) > int(expires_at):
        return False
    
    # Recreate the signature
    if algorithm == 'md5':
        if uri_path is None:
            base_url = getattr(settings, 'GALLERY_MEDIA_BASE_URL', '/media')
            uri_path = f"{base_url}/{quote(file_id)}"
        string_to_sign = f"{uri_path}{expires_at}{secret_key}"
        expected_signature = hashlib.md5(string_to_sign.encode('utf-8')).hexdigest()
        return hmac.compare_digest(expected_signature, signature)
    else:
        # SHA256 verification
        base_url = getattr(settings, 'GALLERY_MEDIA_BASE_URL', '/media')
        uri_path = uri_path or f"{base_url}/{quote(file_id)}"
        string_to_sign = f"{uri_path}{expires_at}{secret_key}"
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).decode('utf-8').rstrip('=')
        signature_padded = signature
        if len(signature_padded) % 4:
            signature_padded += '=' * (4 - len(signature_padded) % 4)
        return hmac.compare_digest(expected_signature_b64, signature_padded)
