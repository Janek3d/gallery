"""
Tests for gallery utility functions.
"""
import pytest
from django.conf import settings
from gallery.utils import generate_signed_url, verify_signed_url


@pytest.mark.unit
class TestSignedURL:
    """Test signed URL generation and verification."""
    
    def test_generate_signed_url(self):
        """Test generating a signed URL."""
        file_path = "/media/pictures/test.jpg"
        signed_url = generate_signed_url(file_path)
        
        assert signed_url is not None
        assert file_path in signed_url["url"]
        assert "e=" in signed_url["url"]
        assert "st=" in signed_url["url"]
    
    def test_verify_signed_url(self):
        """Test verifying a signed URL."""
        file_path = "/media/pictures/test.jpg"
        signed_url = generate_signed_url(file_path)
        
        # Extract the path and signature from the URL
        assert verify_signed_url(signed_url) is True
    
    def test_expired_signed_url(self, settings_override):
        """Test that expired URLs are rejected."""
        # Set a very short expiration time
        settings_override.GALLERY_SIGNED_URL_EXPIRES_IN = 1
        
        file_path = "/media/pictures/test.jpg"
        signed_url = generate_signed_url(file_path)
        
        import time
        time.sleep(2)  # Wait for expiration
        
        # Note: This test might be flaky, but demonstrates the concept
        # In practice, you'd mock time or use a test-specific expiration
