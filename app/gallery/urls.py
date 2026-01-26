"""
URL configuration for Gallery app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GalleryViewSet, AlbumViewSet, PictureViewSet, TagViewSet

router = DefaultRouter()
router.register(r'galleries', GalleryViewSet, basename='gallery')
router.register(r'albums', AlbumViewSet, basename='album')
router.register(r'pictures', PictureViewSet, basename='picture')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('api/', include(router.urls)),
]
