from django.contrib import admin
from .models import Gallery, Album, Picture, PictureTag, GalleryShare, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'usage_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['slug', 'usage_count', 'created_at']
    ordering = ['name']


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'gallery_type', 'is_favorite', 'created_at', 'deleted_at']
    list_filter = ['gallery_type', 'is_favorite', 'tags', 'created_at', 'deleted_at']
    search_fields = ['name', 'description', 'owner__username', 'owner__email', 'tags__name']
    readonly_fields = ['created_at', 'updated_at']
    # filter_horizontal = ['shared_with', 'tags']


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['name', 'gallery', 'created_at', 'deleted_at']
    list_filter = ['tags', 'created_at', 'deleted_at']
    search_fields = ['name', 'description', 'gallery__name', 'tags__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['tags']


class PictureTagInline(admin.TabularInline):
    model = PictureTag
    extra = 0
    autocomplete_fields = ['tag']


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ['title', 'album', 'file_size', 'width', 'height', 'is_favorite', 'uploaded_at', 'deleted_at']
    list_filter = ['is_favorite', 'uploaded_at', 'deleted_at', 'mime_type']
    search_fields = ['title', 'description', 'album__name', 'ocr_text', 'tags__name']
    readonly_fields = ['uploaded_at', 'updated_at', 'seaweedfs_file_id']
    inlines = [PictureTagInline]


@admin.register(GalleryShare)
class GalleryShareAdmin(admin.ModelAdmin):
    list_display = ['gallery', 'user', 'can_edit', 'shared_at']
    list_filter = ['can_edit', 'shared_at']
    search_fields = ['gallery__name', 'user__username', 'user__email']
