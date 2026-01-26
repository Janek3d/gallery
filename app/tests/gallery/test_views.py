"""
Tests for gallery views.
"""
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestGalleryListView:
    """Test gallery list view."""
    
    def test_list_galleries_unauthenticated(self, client):
        """Test that unauthenticated users are redirected to login."""
        url = reverse('gallery:gallery_list')
        response = client.get(url)
        assert response.status_code in [302, 401]  # Redirect or unauthorized
    
    def test_list_galleries_authenticated(self, authenticated_client, user):
        """Test listing galleries for authenticated user."""
        url = reverse('gallery:gallery_list')
        response = authenticated_client.get(url)
        assert response.status_code == 200


@pytest.mark.django_db
class TestGalleryAPIViewSet:
    """Test Gallery API ViewSet."""
    
    def test_list_galleries_api(self, authenticated_api_client, user):
        """Test listing galleries via API."""
        url = reverse('gallery:gallery-list')
        response = authenticated_api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
    
    def test_create_gallery_api(self, authenticated_api_client, user):
        """Test creating a gallery via API."""
        url = reverse('gallery:gallery-list')
        data = {
            'name': 'Test Gallery',
            'description': 'Test description',
            'gallery_type': 'private'
        }
        response = authenticated_api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Test Gallery'
        assert response.data['owner'] == user.id
