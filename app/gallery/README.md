# Gallery Django App

Django app for managing photo galleries with support for SeaweedFS storage and signed URLs.

## Models

### Gallery
- Top-level container for albums
- Tied to User (owner)
- Has type: `private` (default) or `public`
- Fields: name, description, tags, is_favorite
- Supports sharing with other users via `GalleryShare`

### Album
- Container for pictures within a gallery
- Belongs to a Gallery
- Fields: name, description, tags, exif_metadata
- Soft delete support

### Picture
- Individual photo stored on SeaweedFS
- Belongs to an Album
- Stores SeaweedFS file ID and URL
- AI-generated tags (YOLO) and OCR text (PaddleOCR)
- EXIF metadata
- User-defined tags
- Soft delete support

## Features

- **Signed URLs**: Generate secure, time-limited URLs for media files
- **Soft Delete**: All models support soft deletion with `deleted_at` field
- **Sharing**: Galleries can be shared with other users
- **AI Integration**: Support for AI tags and OCR text
- **REST API**: Full REST API using Django REST Framework

## API Endpoints

### Galleries
- `GET /api/galleries/` - List galleries
- `POST /api/galleries/` - Create gallery
- `GET /api/galleries/{id}/` - Get gallery details
- `PUT /api/galleries/{id}/` - Update gallery
- `DELETE /api/galleries/{id}/` - Delete gallery
- `POST /api/galleries/{id}/share/` - Share gallery with users
- `POST /api/galleries/{id}/unshare/` - Remove share access
- `POST /api/galleries/{id}/toggle_favorite/` - Toggle favorite

### Albums
- `GET /api/albums/` - List albums
- `POST /api/albums/` - Create album
- `GET /api/albums/{id}/` - Get album with pictures
- `PUT /api/albums/{id}/` - Update album
- `DELETE /api/albums/{id}/` - Delete album

### Pictures
- `GET /api/pictures/` - List pictures
- `POST /api/pictures/` - Create picture
- `GET /api/pictures/{id}/` - Get picture details
- `PUT /api/pictures/{id}/` - Update picture
- `DELETE /api/pictures/{id}/` - Delete picture
- `GET /api/pictures/{id}/signed_url/` - Get new signed URL
- `POST /api/pictures/{id}/toggle_favorite/` - Toggle favorite
- `POST /api/pictures/{id}/add_tag/` - Add tag
- `POST /api/pictures/{id}/remove_tag/` - Remove tag

## Signed URLs

Signed URLs are generated using MD5 (compatible with Nginx `secure_link` module):

```python
from gallery.utils import generate_signed_url

signed = generate_signed_url('file-id-123', expires_in=3600)
# Returns: {
#     'url': '/media/file-id-123?st=signature&e=1234567890',
#     'expires_at': 1234567890,
#     'expires_in': 3600
# }
```

URLs are validated by Nginx before serving files. See `docs/NGINX_SIGNED_URLS.md` for configuration.

## Settings

Add to `settings.py`:

```python
# Gallery App Configuration
GALLERY_MEDIA_BASE_URL = '/media'
GALLERY_SIGNED_URL_SECRET = 'your-secret-key'  # Optional, defaults to SECRET_KEY
GALLERY_SIGNED_URL_EXPIRES_IN = 3600  # 1 hour default
```

## Usage Example

```python
from gallery.models import Gallery, Album, Picture
from gallery.utils import generate_signed_url

# Create gallery
gallery = Gallery.objects.create(
    owner=user,
    name="My Vacation",
    gallery_type=Gallery.GalleryType.PRIVATE
)

# Create album
album = Album.objects.create(
    gallery=gallery,
    name="Beach Photos"
)

# Create picture
picture = Picture.objects.create(
    album=album,
    title="Sunset",
    seaweedfs_file_id="abc123",
    seaweedfs_url="http://seaweedfs:8888/abc123"
)

# Generate signed URL
signed_url = generate_signed_url(picture.seaweedfs_file_id)
print(signed_url['url'])  # /media/abc123?st=...&e=...
```

## Permissions

- Users can only access galleries they own or that are shared with them
- Gallery owners can share/unshare galleries
- Shared users have read-only access by default (can be set to edit)

## Soft Delete

All models support soft deletion:

```python
gallery.soft_delete()  # Sets deleted_at
gallery.restore()      # Clears deleted_at
gallery.is_deleted     # Check if deleted
```

Soft-deleted items are automatically excluded from querysets.
