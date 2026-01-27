"""
Tests for gallery utility functions.
"""
import pytest
from urllib.parse import urlparse, parse_qs, unquote
from django.conf import settings
from gallery.utils import generate_signed_url, verify_signed_url


@pytest.mark.unit
class TestSignedURL:
    """Test signed URL generation and verification."""
    
    def test_generate_signed_url(self):
        """Test generating a signed URL."""
        file_id = "01637037d6"  # SeaweedFS file ID format (alphanumeric)
        result = generate_signed_url(file_id)
        
        assert result is not None
        assert isinstance(result, dict)
        assert "url" in result
        assert "expires_at" in result
        assert "expires_in" in result
        
        signed_url = result["url"]
        # Parse URL to extract file_id from path (accounting for URL encoding)
        parsed_url = urlparse(signed_url)
        path_file_id = unquote(parsed_url.path.split('/')[-1])
        assert path_file_id == file_id
        assert "e=" in signed_url
        assert "st=" in signed_url
    
    def test_verify_signed_url(self):
        """Test verifying a signed URL."""
        file_id = "01637037d6"  # SeaweedFS file ID format (alphanumeric)
        result = generate_signed_url(file_id)
        
        # Parse the URL to extract signature and expires_at
        parsed_url = urlparse(result["url"])
        query_params = parse_qs(parsed_url.query)
        signature = query_params["st"][0]
        expires_at = int(query_params["e"][0])
        
        # Verify the signed URL with all necessary arguments
        assert verify_signed_url(file_id, signature, expires_at) is True
    
    def test_expired_signed_url(self, settings_override):
        """Test that expired URLs are rejected."""
        # Set a very short expiration time
        settings_override.GALLERY_SIGNED_URL_EXPIRES_IN = 1
        
        file_id = "01637037d6"  # SeaweedFS file ID format (alphanumeric)
        result = generate_signed_url(file_id, expires_in=1)
        
        # Parse the URL to extract signature and expires_at
        parsed_url = urlparse(result["url"])
        query_params = parse_qs(parsed_url.query)
        signature = query_params["st"][0]
        expires_at = int(query_params["e"][0])
        
        import time
        time.sleep(2)  # Wait for expiration
        
        # Verify that expired URL is rejected
        assert verify_signed_url(file_id, signature, expires_at) is False
        
        # Note: This test might be flaky, but demonstrates the concept
        # In practice, you'd mock time or use a test-specific expiration
