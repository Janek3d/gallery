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
        assert not gallery.is_deleted
        
        gallery.soft_delete()
        gallery.refresh_from_db()
        assert gallery.deleted_at is not None
        assert gallery.is_deleted
        
        # Gallery still exists in database (soft delete doesn't remove it)
        assert Gallery.objects.filter(pk=gallery.pk).exists()
        
        # But should not appear in filtered queryset (non-deleted only)
        assert Gallery.objects.filter(pk=gallery.pk, deleted_at__isnull=True).count() == 0
    
    def test_gallery_tags(self, user):
        """Test adding and removing tags."""
        gallery = Gallery.objects.create(
            owner=user,
            name="Test Gallery"
        )
        
        tag1, _ = Tag.get_or_create_tag("vacation")
        tag2, _ = Tag.get_or_create_tag("beach")
        
        # Tags start with usage_count = 0
        assert tag1.usage_count == 0
        assert tag2.usage_count == 0
        
        gallery.add_tag("vacation")
        gallery.add_tag("beach")
        
        # Refresh tags to get updated usage_count
        tag1.refresh_from_db()
        tag2.refresh_from_db()

        tags = gallery.tags.all()
        
        assert gallery.tags.count() == 2
        assert tag1 in tags
        assert tag2 in tags
        # usage_count should be incremented when tags are added
        assert tag1.usage_count == 1
        assert tag2.usage_count == 1
        
        gallery.remove_tag("vacation")
        tag1.refresh_from_db()
        assert gallery.tags.count() == 1
        assert tag1 not in gallery.tags.all()
        # usage_count should be decremented when tag is removed
        assert tag1.usage_count == 0


@pytest.mark.django_db
class TestTagModel:
    """Test Tag model."""
    
    def test_create_tag(self):
        """Test creating a tag."""
        tag, created = Tag.get_or_create_tag("test-tag")
        assert tag.name == "test-tag"
        assert tag.slug == "test-tag"
        # usage_count should be 0 when tag is first created (not used yet)
        assert tag.usage_count == 0
    
    def test_tag_normalization(self):
        """Test tag name normalization."""
        tag1, _ = Tag.get_or_create_tag("Test Tag")
        tag2, _ = Tag.get_or_create_tag("test tag")
        tag3, _ = Tag.get_or_create_tag("TEST TAG")
        
        # All should be the same tag
        assert tag1 == tag2 == tag3
        assert tag1.name == "test tag"
    
    def test_tag_usage_count(self):
        """Test tag usage count tracking."""
        tag, _ = Tag.get_or_create_tag("test")
        # Initially 0 when tag is created but not used
        assert tag.usage_count == 0
        
        tag.increment_usage()
        tag.refresh_from_db()
        assert tag.usage_count == 1
        
        tag.increment_usage()
        tag.refresh_from_db()
        assert tag.usage_count == 2
        
        tag.decrement_usage()
        tag.refresh_from_db()
        assert tag.usage_count == 1
        
        tag.decrement_usage()
        tag.refresh_from_db()
        assert tag.usage_count == 0
