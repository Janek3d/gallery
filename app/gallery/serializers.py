"""
DRF serializers for Gallery API
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Gallery, Album, Picture, GalleryShare, Tag
from .utils import generate_signed_url

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'usage_count']
        read_only_fields = ['slug', 'usage_count']


class TagListField(serializers.Field):
    """Custom field to handle tags as list of names"""
    def to_representation(self, value):
        """Convert Tag queryset to list of tag names"""
        return [tag.name for tag in value.all()]
    
    def to_internal_value(self, data):
        """Convert list of tag names to Tag objects"""
        if not isinstance(data, list):
            raise serializers.ValidationError("Tags must be a list of tag names")
        return data


class PictureSerializer(serializers.ModelSerializer):
    """Serializer for Picture model with signed URL"""
    signed_url = serializers.SerializerMethodField()
    all_tags = serializers.SerializerMethodField()
    tags = TagListField()
    album_name = serializers.CharField(source='album.name', read_only=True)
    
    class Meta:
        model = Picture
        fields = [
            'id', 'title', 'description', 'album', 'album_name',
            'seaweedfs_file_id', 'signed_url', 'file_size', 'mime_type',
            'width', 'height', 'ai_tags', 'ocr_text', 'exif_data',
            'tags', 'all_tags', 'is_favorite', 'taken_at',
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = [
            'seaweedfs_file_id', 'signed_url', 'file_size', 'mime_type',
            'width', 'height', 'uploaded_at', 'updated_at'
        ]
    
    def get_signed_url(self, obj):
        """Generate signed URL for the picture"""
        if not obj.seaweedfs_file_id:
            return None
        try:
            signed = generate_signed_url(obj.seaweedfs_file_id)
            return signed['url']
        except Exception:
            return None
    
    def get_all_tags(self, obj):
        """Get all tags (user tags + AI tags)"""
        return obj.all_tags
    
    def update(self, instance, validated_data):
        """Handle tag updates"""
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        
        if tags_data is not None:
            instance.set_tags(tags_data)
        
        return instance
    
    def create(self, validated_data):
        """Handle tag creation"""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        if tags_data:
            instance.set_tags(tags_data)
        
        return instance


class AlbumSerializer(serializers.ModelSerializer):
    """Serializer for Album model"""
    picture_count = serializers.SerializerMethodField()
    tags = TagListField()
    gallery_name = serializers.CharField(source='gallery.name', read_only=True)
    
    class Meta:
        model = Album
        fields = [
            'id', 'name', 'description', 'gallery', 'gallery_name',
            'tags', 'exif_metadata', 'picture_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_picture_count(self, obj):
        """Get count of non-deleted pictures"""
        return obj.pictures.filter(deleted_at__isnull=True).count()
    
    def update(self, instance, validated_data):
        """Handle tag updates"""
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        
        if tags_data is not None:
            instance.set_tags(tags_data)
        
        return instance
    
    def create(self, validated_data):
        """Handle tag creation"""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        if tags_data:
            instance.set_tags(tags_data)
        
        return instance


class AlbumDetailSerializer(AlbumSerializer):
    """Detailed album serializer with pictures"""
    pictures = PictureSerializer(many=True, read_only=True)
    
    class Meta(AlbumSerializer.Meta):
        fields = AlbumSerializer.Meta.fields + ['pictures']


class GalleryShareSerializer(serializers.ModelSerializer):
    """Serializer for GalleryShare"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = GalleryShare
        fields = ['id', 'user', 'user_email', 'user_username', 'can_edit', 'shared_at']
        read_only_fields = ['shared_at']


class GallerySerializer(serializers.ModelSerializer):
    """Serializer for Gallery model"""
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    album_count = serializers.SerializerMethodField()
    tags = TagListField()
    shared_with_users = GalleryShareSerializer(source='shares', many=True, read_only=True)
    
    class Meta:
        model = Gallery
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username',
            'gallery_type', 'tags', 'is_favorite', 'album_count',
            'shared_with_users', 'created_at', 'updated_at'
        ]
        read_only_fields = ['owner', 'created_at', 'updated_at']
    
    def get_album_count(self, obj):
        """Get count of non-deleted albums"""
        return obj.albums.filter(deleted_at__isnull=True).count()
    
    def update(self, instance, validated_data):
        """Handle tag updates"""
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        
        if tags_data is not None:
            instance.set_tags(tags_data)
        
        return instance
    
    def create(self, validated_data):
        """Handle tag creation"""
        tags_data = validated_data.pop('tags', [])
        instance = super().create(validated_data)
        
        if tags_data:
            instance.set_tags(tags_data)
        
        return instance


class GalleryDetailSerializer(GallerySerializer):
    """Detailed gallery serializer with albums"""
    albums = AlbumSerializer(many=True, read_only=True)
    
    class Meta(GallerySerializer.Meta):
        fields = GallerySerializer.Meta.fields + ['albums']
