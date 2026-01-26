"""
Tests for gallery models.
"""
import pytest
from django.contrib.auth import get_user_model
from gallery.models import Gallery, Album, Picture, Tag

User = get_user_model()


@pytest.mark.django_db
class TestGalleryModel:
    """Test Gallery model."""
    
    def test_create_gallery(self, user):
        """Test creating a gallery."""
        gallery = Gallery.objects.create(
            owner=user,
            name="Test Gallery",
            description="Test description",
            gallery_type="private"
        )
        # print(gallery)
        assert gallery.name == "Test Gallery"
        assert gallery.owner == user
        assert gallery.gallery_type == "private"
        assert not gallery.is_favorite
    
    def test_gallery_soft_delete(self, user):
        """Test soft delete functionality."""
        gallery = Gallery.objects.create(
            owner=user,
            name="Test Gallery"
        )
        assert gallery.deleted_at is None
        
        gallery.soft_delete()
        assert gallery.deleted_at is not None
        
        # Should not appear in default queryset
        assert Gallery.objects.filter(pk=gallery.pk).count() == 0
    
    def test_gallery_tags(self, user):
        """Test adding and removing tags."""
        gallery = Gallery.objects.create(
            owner=user,
            name="Test Gallery"
        )
        
        tag1 = Tag.get_or_create_tag("vacation")
        tag2 = Tag.get_or_create_tag("beach")
        
        gallery.add_tag("vacation")
        gallery.add_tag("beach")
        
        assert gallery.tags.count() == 2
        assert tag1 in gallery.tags.all()
        assert tag2 in gallery.tags.all()
        
        gallery.remove_tag("vacation")
        assert gallery.tags.count() == 1
        assert tag1 not in gallery.tags.all()


@pytest.mark.django_db
class TestTagModel:
    """Test Tag model."""
    
    def test_create_tag(self):
        """Test creating a tag."""
        tag, created = Tag.get_or_create_tag("test-tag")
        assert tag.name == "test-tag"
        assert tag.slug == "test-tag"
        assert tag.usage_count == 1
    
    def test_tag_normalization(self):
        """Test tag name normalization."""
        tag1 = Tag.get_or_create_tag("Test Tag")
        tag2 = Tag.get_or_create_tag("test tag")
        tag3 = Tag.get_or_create_tag("TEST TAG")
        
        # All should be the same tag
        assert tag1 == tag2 == tag3
        assert tag1.name == "test tag"
    
    def test_tag_usage_count(self):
        """Test tag usage count tracking."""
        tag = Tag.get_or_create_tag("test")
        assert tag.usage_count == 1
        
        tag.increment_usage()
        tag.refresh_from_db()
        assert tag.usage_count == 2
        
        tag.decrement_usage()
        tag.refresh_from_db()
        assert tag.usage_count == 1
