"""
URL configuration for Gallery app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GalleryViewSet, AlbumViewSet, PictureViewSet, TagViewSet
from . import template_views

app_name = 'gallery'

# API routes
router = DefaultRouter()
router.register(r'galleries', GalleryViewSet, basename='gallery')
router.register(r'albums', AlbumViewSet, basename='album')
router.register(r'pictures', PictureViewSet, basename='picture')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    
    # Template-based routes
    path('', template_views.gallery_list, name='gallery_list'),
    path('galleries/create/', template_views.gallery_create, name='gallery_create'),
    path('galleries/<int:pk>/', template_views.gallery_detail, name='gallery_detail'),
    path('galleries/<int:pk>/edit/', template_views.gallery_edit, name='gallery_edit'),
    
    # HTMX endpoints for galleries
    path('galleries/<int:pk>/toggle-favorite/', template_views.gallery_toggle_favorite, name='gallery_toggle_favorite'),
    path('galleries/<int:pk>/add-tag/', template_views.gallery_add_tag, name='gallery_add_tag'),
    path('galleries/<int:pk>/remove-tag/', template_views.gallery_remove_tag, name='gallery_remove_tag'),
    
    # Albums
    path('albums/<int:pk>/', template_views.album_detail, name='album_detail'),
    path('galleries/<int:gallery_id>/albums/create/', template_views.album_create, name='album_create'),
    
    # HTMX endpoints for albums
    path('albums/<int:pk>/add-tag/', template_views.album_add_tag, name='album_add_tag'),
    path('albums/<int:pk>/remove-tag/', template_views.album_remove_tag, name='album_remove_tag'),
    
    # Pictures
    path('pictures/<int:pk>/', template_views.picture_detail, name='picture_detail'),
    
    # HTMX endpoints for pictures
    path('pictures/<int:pk>/toggle-favorite/', template_views.picture_toggle_favorite, name='picture_toggle_favorite'),
]
