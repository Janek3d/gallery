"""
Utility functions for Gallery app, including signed URL generation for SeaweedFS
"""
import hmac
import hashlib
import base64
import io
import time
import uuid
import zipfile
import tarfile
from urllib.parse import urlencode, quote
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
import logging

logger = logging.getLogger(__name__)

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
        signature = hashlib.md5(string_to_sign.encode('utf-8')).digest()
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
    # logger.info(f"{string_to_sign=} {len(string_to_sign)=} {repr(string_to_sign)} | {signature=} {len(signature)=} {repr(signature)} | {uri_path=} | {expires_at=} | {signed_url=}")
    
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
        expected_signature = hashlib.md5(string_to_sign.encode('utf-8')).digest()
        expected_signature_b64 = base64.urlsafe_b64encode(expected_signature).rstrip(b'=')
        return hmac.compare_digest(expected_signature_b64, signature)
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


def upload_picture_file(file, album_id, content_type=None):
    """
    Save an uploaded picture file to storage (S3/SeaweedFS or local MEDIA_ROOT).
    Returns the storage path to use as seaweedfs_file_id for the Picture model.

    Args:
        file: Uploaded file object (Django UploadedFile)
        album_id: Album id (used in path)
        content_type: Optional MIME type (defaults to file.content_type)

    Returns:
        str: Storage path/key to store in Picture.seaweedfs_file_id
    """
    ext = (file.name or '').split('.')[-1].lower() or 'jpg'
    if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif'):
        ext = 'jpg'
    name = f'pictures/{album_id}/{uuid.uuid4().hex}.{ext}'
    path = default_storage.save(name, file)
    return path


IMAGE_EXTENSIONS = frozenset(('jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'heif'))


def _is_image_filename(name):
    if not name or '/' in name or '\\' in name:
        return False
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
    return ext in IMAGE_EXTENSIONS


def extract_images_from_archive(archive_file, max_size=100 * 1024 * 1024):
    """
    Extract image files from a ZIP or TAR archive.
    Yields (filename, file_like_object) for each image.
    Skips non-image entries. Raises ValueError for invalid or too-large archives.

    Args:
        archive_file: Django UploadedFile (ZIP or TAR/TAR.GZ)
        max_size: Max total uncompressed size to process (default 100MB)

    Yields:
        tuple: (original_filename, file-like object with .read(), .name, .size)
    """
    name = (getattr(archive_file, 'name', '') or '').lower()
    archive_file.seek(0)
    total_size = 0

    if name.endswith('.zip'):
        with zipfile.ZipFile(archive_file, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if not _is_image_filename(info.filename):
                    continue
                total_size += info.file_size
                if total_size > max_size:
                    raise ValueError(f'Archive exceeds maximum size ({max_size // (1024*1024)}MB)')
                data = zf.read(info.filename)
                yield (info.filename, SimpleUploadedFile(
                    name=info.filename.rsplit('/')[-1],
                    content=data,
                    content_type='application/octet-stream',
                ))
    elif name.endswith('.tar') or name.endswith('.tar.gz') or name.endswith('.tgz'):
        mode = 'r:gz' if ('.gz' in name or name.endswith('.tgz')) else 'r'
        with tarfile.open(fileobj=archive_file, mode=mode) as tf:
            for member in tf.getmembers():
                if not member.isfile():
                    continue
                if not _is_image_filename(member.name):
                    continue
                total_size += member.size
                if total_size > max_size:
                    raise ValueError(f'Archive exceeds maximum size ({max_size // (1024*1024)}MB)')
                f = tf.extractfile(member)
                if f is None:
                    continue
                data = f.read()
                yield (member.name, SimpleUploadedFile(
                    name=member.name.rsplit('/')[-1],
                    content=data,
                    content_type='application/octet-stream',
                ))
    else:
        raise ValueError('Unsupported archive format. Use .zip, .tar, or .tar.gz')
