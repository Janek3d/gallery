"""
API views for Gallery app
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Gallery, Album, Picture, GalleryShare, Tag
from .serializers import (
    GallerySerializer, GalleryDetailSerializer,
    AlbumSerializer, AlbumDetailSerializer,
    PictureSerializer, TagSerializer
)
from .utils import generate_signed_url


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Tag operations (read-only, tags are managed through objects)
    """
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'slug']
    
    def get_queryset(self):
        """Get tags used by the user's galleries/albums/pictures"""
        user = self.request.user
        # Get tags from user's galleries, albums, and pictures
        gallery_tags = Tag.objects.filter(galleries__owner=user).distinct()
        album_tags = Tag.objects.filter(albums__gallery__owner=user).distinct()
        picture_tags = Tag.objects.filter(pictures__album__gallery__owner=user).distinct()
        
        return (gallery_tags | album_tags | picture_tags).distinct().order_by('name')
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular tags"""
        limit = int(request.query_params.get('limit', 20))
        tags = Tag.objects.filter(usage_count__gt=0).order_by('-usage_count')[:limit]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class GalleryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Gallery operations
    """
    serializer_class = GallerySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get galleries accessible by the user"""
        user = self.request.user
        queryset = Gallery.objects.filter(
            Q(owner=user) | Q(shared_with=user),
            deleted_at__isnull=True
        ).distinct()
        
        # Filter by tags if provided
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve action"""
        if self.action == 'retrieve':
            return GalleryDetailSerializer
        return GallerySerializer
    
    def perform_create(self, serializer):
        """Set owner to current user"""
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Share gallery with users by email"""
        gallery = get_object_or_404(Gallery, pk=pk, deleted_at__isnull=True)
        
        # Check permission - only owner can share
        if gallery.owner != request.user:
            return Response(
                {'error': 'Only gallery owner can share'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        emails = request.data.get('emails', [])
        can_edit = request.data.get('can_edit', False)
        
        if not isinstance(emails, list):
            return Response(
                {'error': 'emails must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shared_users = []
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        for email in emails:
            try:
                user = User.objects.get(email=email)
                share, created = GalleryShare.objects.get_or_create(
                    gallery=gallery,
                    user=user,
                    defaults={'can_edit': can_edit}
                )
                if not created:
                    share.can_edit = can_edit
                    share.save()
                shared_users.append(user.email)
            except User.DoesNotExist:
                # Could send invitation email here
                pass
        
        return Response({
            'message': f'Gallery shared with {len(shared_users)} users',
            'shared_with': shared_users
        })
    
    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """Remove share access for a user"""
        gallery = self.get_object()
        
        if gallery.owner != request.user:
            return Response(
                {'error': 'Only gallery owner can unshare'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        GalleryShare.objects.filter(gallery=gallery, user_id=user_id).delete()
        
        return Response({'message': 'Share access removed'})
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status"""
        gallery = self.get_object()
        gallery.is_favorite = not gallery.is_favorite
        gallery.save(update_fields=['is_favorite'])
        return Response({'is_favorite': gallery.is_favorite})


class AlbumViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Album operations
    """
    serializer_class = AlbumSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get albums accessible by the user"""
        user = self.request.user
        gallery_id = self.request.query_params.get('gallery_id')
        
        queryset = Album.objects.filter(
            gallery__owner=user,
            deleted_at__isnull=True
        ) | Album.objects.filter(
            gallery__shared_with=user,
            deleted_at__isnull=True
        )
        
        if gallery_id:
            queryset = queryset.filter(gallery_id=gallery_id)
        
        # Filter by tags if provided
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        
        return queryset.distinct()
    
    def get_serializer_class(self):
        """Use detail serializer for retrieve action"""
        if self.action == 'retrieve':
            return AlbumDetailSerializer
        return AlbumSerializer
    
    def perform_create(self, serializer):
        """Check permission and create album"""
        gallery = serializer.validated_data['gallery']
        
        # Check if user has access to gallery
        if gallery.owner != self.request.user and not gallery.shared_with.filter(id=self.request.user.id).exists():
            raise PermissionError('You do not have access to this gallery')
        
        serializer.save()


class PictureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Picture operations
    """
    serializer_class = PictureSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Get pictures accessible by the user"""
        user = self.request.user
        album_id = self.request.query_params.get('album_id')
        
        queryset = Picture.objects.filter(
            album__gallery__owner=user,
            deleted_at__isnull=True
        ) | Picture.objects.filter(
            album__gallery__shared_with=user,
            deleted_at__isnull=True
        )
        
        if album_id:
            queryset = queryset.filter(album_id=album_id)
        
        # Filter by tags if provided
        tags = self.request.query_params.getlist('tags')
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()
        
        return queryset.distinct()
    
    @action(detail=True, methods=['get'])
    def signed_url(self, request, pk=None):
        """Get a new signed URL for the picture"""
        picture = self.get_object()
        
        expires_in = int(request.query_params.get('expires_in', 3600))
        signed = generate_signed_url(picture.seaweedfs_file_id, expires_in=expires_in)
        
        return Response(signed)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """Toggle favorite status"""
        picture = self.get_object()
        picture.is_favorite = not picture.is_favorite
        picture.save(update_fields=['is_favorite'])
        return Response({'is_favorite': picture.is_favorite})
    
    @action(detail=True, methods=['post'])
    def add_tag(self, request, pk=None):
        """Add a tag to the picture"""
        picture = self.get_object()
        tag_name = request.data.get('tag')
        
        if not tag_name:
            return Response(
                {'error': 'tag is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        picture.add_tag(tag_name)
        tag_names = [tag.name for tag in picture.tags.all()]
        
        return Response({'tags': tag_names})
    
    @action(detail=True, methods=['post'])
    def remove_tag(self, request, pk=None):
        """Remove a tag from the picture"""
        picture = self.get_object()
        tag_name = request.data.get('tag')
        
        if not tag_name:
            return Response(
                {'error': 'tag is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        picture.remove_tag(tag_name)
        tag_names = [tag.name for tag in picture.tags.all()]
        
        return Response({'tags': tag_names})
