# Nginx Signed URL Configuration

This document explains how to configure Nginx to validate signed URLs for SeaweedFS media files.

## Overview

Django generates signed URLs for pictures stored in SeaweedFS. Nginx validates these URLs using the `secure_link` module before serving the files.

## URL Format

Signed URLs have the format:
```
/media/{file_id}?st={signature}&e={expires_timestamp}
```

Where:
- `st`: HMAC-SHA256 signature (base64url encoded)
- `e`: Unix timestamp when URL expires

## Nginx Configuration

The Nginx configuration uses the `secure_link` module to validate URLs:

```nginx
location /media/ {
    secure_link $arg_st,$arg_e;
    secure_link_md5 "$uri$secure_link_expires$secure_link_secret";
    
    if ($secure_link = "") {
        return 403;
    }
    if ($secure_link = "0") {
        return 403;
    }
    
    # Proxy to SeaweedFS or serve locally
    proxy_pass http://seaweedfs:8888/;
    # OR
    alias /media/;
}
```

## Setting the Secret Key

The `secure_link_secret` must match the secret used by Django. Set it in Nginx:

### Option 1: Environment Variable (Recommended)

In `docker-compose.yml`:
```yaml
nginx:
  environment:
    - SECURE_LINK_SECRET=${GALLERY_SIGNED_URL_SECRET:-${SECRET_KEY}}
```

Then in Nginx config:
```nginx
secure_link_secret $SECURE_LINK_SECRET;
```

### Option 2: Direct Configuration

```nginx
secure_link_secret "your-secret-key-here";
```

**Important:** This secret must match:
- Django `GALLERY_SIGNED_URL_SECRET` setting, OR
- Django `SECRET_KEY` if `GALLERY_SIGNED_URL_SECRET` is not set

## How It Works

1. **Django generates signed URL:**
   ```python
   from gallery.utils import generate_signed_url
   signed = generate_signed_url(file_id, expires_in=3600)
   # Returns: /media/{file_id}?st={signature}&e={expires}
   ```

2. **Browser requests the URL:**
   ```
   GET /media/abc123?st=xyz&e=1234567890
   ```

3. **Nginx validates:**
   - Extracts `st` (signature) and `e` (expires) from query params
   - Recomputes signature using: `HMAC-SHA256(uri + expires + secret)`
   - Compares with provided signature
   - Checks if current time < expires timestamp
   - Returns 403 if invalid or expired

4. **If valid, serves file:**
   - Proxies to SeaweedFS, OR
   - Serves from local storage

## Testing

### Generate a test URL in Django shell:
```python
from gallery.utils import generate_signed_url
signed = generate_signed_url("test-file-id", expires_in=3600)
print(signed['url'])
```

### Test with curl:
```bash
# Valid URL
curl "http://localhost/media/test-file-id?st=...&e=..."

# Invalid signature (should return 403)
curl "http://localhost/media/test-file-id?st=wrong&e=1234567890"

# Expired URL (should return 403)
curl "http://localhost/media/test-file-id?st=...&e=1"
```

## Security Notes

1. **Secret Key:** Keep the secret key secure and never expose it
2. **Expiration:** URLs expire after the specified time (default 1 hour)
3. **HTTPS:** Use HTTPS in production to prevent URL interception
4. **Rate Limiting:** Consider adding rate limiting for media endpoints

## Troubleshooting

### 403 Forbidden Errors

1. Check that `secure_link_secret` matches Django's secret
2. Verify URL format is correct
3. Check if URL has expired
4. Verify Nginx has `secure_link` module enabled:
   ```bash
   nginx -V 2>&1 | grep -o with-http_secure_link_module
   ```

### Module Not Found

If `secure_link` module is not available, you may need to:
- Recompile Nginx with `--with-http_secure_link_module`
- Use a different Nginx image that includes the module
- Use an alternative validation method (e.g., Django middleware)
