"""
Template-based views for Gallery app with HTMX support
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.template.loader import render_to_string
from .models import Gallery, Album, Picture, Tag
from .forms import GalleryForm, AlbumForm, PictureUploadForm
from .utils import generate_signed_url, upload_picture_file, extract_images_from_archive
import logging

logger = logging.getLogger(__name__)

@login_required
def gallery_list(request):
    """List all galleries for the user"""
    user = request.user
    shared = request.GET.get('shared') == '1'
    
    if shared:
        galleries = Gallery.objects.filter(
            shared_with=user,
            deleted_at__isnull=True
        ).distinct()
    else:
        galleries = Gallery.objects.filter(
            owner=user,
            deleted_at__isnull=True
        )
    
    # Filter by search
    search = request.GET.get('search')
    if search:
        galleries = galleries.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search) |
            Q(tags__name__icontains=search)
        ).distinct()
    
    # Filter by type
    gallery_type = request.GET.get('gallery_type')
    if gallery_type:
        galleries = galleries.filter(gallery_type=gallery_type)
    
    # Prefetch related
    galleries = galleries.prefetch_related('tags', 'albums').order_by('-created_at')
    
    context = {
        'galleries': galleries,
    }
    return render(request, 'gallery/gallery_list.html', context)


@login_required
def gallery_detail(request, pk):
    """View gallery details"""
    gallery = get_object_or_404(
        Gallery.objects.filter(
            Q(owner=request.user) | Q(shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    # Prefetch albums with pictures
    albums = gallery.albums.filter(deleted_at__isnull=True).prefetch_related('pictures', 'tags')
    
    context = {
        'gallery': gallery,
        'albums': albums,
    }
    return render(request, 'gallery/gallery_detail.html', context)


@login_required
def gallery_create(request):
    """Create a new gallery"""
    if request.method == 'POST':
        form = GalleryForm(request.POST)
        if form.is_valid():
            gallery = form.save(commit=False)
            gallery.owner = request.user
            gallery.save()
            
            # Handle tags
            tags_str = request.POST.get('tags', '')
            if tags_str:
                tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                gallery.set_tags(tag_names)
            
            messages.success(request, f'Gallery "{gallery.name}" created successfully!')
            return redirect('gallery:gallery_detail', pk=gallery.id)
    else:
        form = GalleryForm()
    
    context = {'form': form}
    return render(request, 'gallery/gallery_form.html', context)


@login_required
def gallery_edit(request, pk):
    """Edit a gallery"""
    gallery = get_object_or_404(Gallery, pk=pk, owner=request.user, deleted_at__isnull=True)
    
    if request.method == 'POST':
        form = GalleryForm(request.POST, instance=gallery)
        if form.is_valid():
            gallery = form.save()
            messages.success(request, f'Gallery "{gallery.name}" updated successfully!')
            return redirect('gallery:gallery_detail', pk=gallery.id)
    else:
        form = GalleryForm(instance=gallery)
    
    context = {'form': form, 'gallery': gallery}
    return render(request, 'gallery/gallery_form.html', context)


@login_required
@require_http_methods(["POST"])
def gallery_toggle_favorite(request, pk):
    """Toggle favorite status (HTMX endpoint)"""
    gallery = get_object_or_404(
        Gallery.objects.filter(
            Q(owner=request.user) | Q(shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    gallery.is_favorite = not gallery.is_favorite
    gallery.save(update_fields=['is_favorite'])
    
    # Return updated button HTML for HTMX
    button_html = render_to_string('gallery/partials/favorite_button.html', {
        'object': gallery,
        'object_type': 'gallery',
        'object_id': gallery.id,
    }, request=request)
    
    return HttpResponse(button_html)


@login_required
@require_http_methods(["POST"])
def gallery_add_tag(request, pk):
    """Add tag to gallery (HTMX endpoint)"""
    gallery = get_object_or_404(
        Gallery.objects.filter(
            Q(owner=request.user) | Q(shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    tag_name = request.POST.get('tag', '').strip()
    if tag_name:
        gallery.add_tag(tag_name)
    
    # Return updated tags HTML for HTMX
    tags_html = render_to_string('gallery/partials/tags_list.html', {
        'object': gallery,
        'object_type': 'gallery',
        'object_id': gallery.id,
    }, request=request)
    
    return HttpResponse(tags_html)


@login_required
@require_http_methods(["POST", "DELETE"])
def gallery_remove_tag(request, pk):
    """Remove tag from gallery (HTMX endpoint)"""
    gallery = get_object_or_404(
        Gallery.objects.filter(
            Q(owner=request.user) | Q(shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    # HTMX sends DELETE but Django forms send POST
    tag_name = request.POST.get('tag', '').strip()
    if tag_name:
        gallery.remove_tag(tag_name)
    
    # Return empty string to remove the tag element
    return HttpResponse('')


@login_required
def album_detail(request, pk):
    """View album details"""
    album = get_object_or_404(
        Album.objects.filter(
            Q(gallery__owner=request.user) | Q(gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    # Generate signed URLs for pictures (set on same objects passed to template)
    pictures = album.pictures.filter(deleted_at__isnull=True).prefetch_related('tags')
    for picture in pictures:
        if picture.seaweedfs_file_id:
            try:
                signed = generate_signed_url(picture.seaweedfs_file_id)
                picture.signed_url = signed['url']
            except Exception:
                picture.signed_url = None
        else:
            picture.signed_url = None
    context = {
        'album': album,
        'pictures': pictures,
    }
    return render(request, 'gallery/album_detail.html', context)


@login_required
def album_create(request, gallery_id):
    """Create a new album"""
    gallery = get_object_or_404(
        Gallery.objects.filter(
            Q(owner=request.user) | Q(shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=gallery_id
    )
    
    if request.method == 'POST':
        form = AlbumForm(request.POST, gallery=gallery)
        if form.is_valid():
            album = form.save()
            
            # Handle tags
            tags_str = request.POST.get('tags', '')
            if tags_str:
                tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
                album.set_tags(tag_names)
            
            messages.success(request, f'Album "{album.name}" created successfully!')
            return redirect('gallery:album_detail', pk=album.id)
    else:
        form = AlbumForm(gallery=gallery)
    
    context = {'form': form, 'gallery': gallery}
    return render(request, 'gallery/album_form.html', context)


@login_required
def album_edit(request, pk):
    """Edit an album"""
    album = get_object_or_404(
        Album.objects.filter(
            Q(gallery__owner=request.user) | Q(gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    if request.method == 'POST':
        form = AlbumForm(request.POST, instance=album)
        if form.is_valid():
            album = form.save()
            messages.success(request, f'Album "{album.name}" updated successfully!')
            return redirect('gallery:album_detail', pk=album.id)
    else:
        form = AlbumForm(instance=album)
    
    context = {'form': form, 'album': album, 'gallery': album.gallery}
    return render(request, 'gallery/album_form.html', context)


@login_required
@require_http_methods(["POST"])
def album_add_tag(request, pk):
    """Add tag to album (HTMX endpoint)"""
    album = get_object_or_404(
        Album.objects.filter(
            Q(gallery__owner=request.user) | Q(gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    tag_name = request.POST.get('tag', '').strip()
    if tag_name:
        album.add_tag(tag_name)
    
    # Return updated tags HTML for HTMX
    tags_html = render_to_string('gallery/partials/tags_list.html', {
        'object': album,
        'object_type': 'album',
        'object_id': album.id,
    }, request=request)
    
    return HttpResponse(tags_html)


@login_required
@require_http_methods(["POST", "DELETE"])
def album_remove_tag(request, pk):
    """Remove tag from album (HTMX endpoint)"""
    album = get_object_or_404(
        Album.objects.filter(
            Q(gallery__owner=request.user) | Q(gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    # HTMX sends DELETE but Django forms send POST
    tag_name = request.POST.get('tag', '').strip()
    if tag_name:
        album.remove_tag(tag_name)
    
    # Return empty string to remove the tag element
    return HttpResponse('')


def _process_uploaded_image(uploaded_file, album, form_cleaned_data):
    """Process a single uploaded image: get dimensions, upload to storage, create Picture, add tags."""
    width, height = None, None
    try:
        from PIL import Image
        img = Image.open(uploaded_file)
        width, height = img.size
        uploaded_file.seek(0)
    except Exception:
        pass

    file_id = upload_picture_file(
        uploaded_file,
        album_id=album.id,
        content_type=getattr(uploaded_file, 'content_type', None),
    )
    title = form_cleaned_data.get('title') or (getattr(uploaded_file, 'name', '') or 'Untitled')
    if title == 'Untitled' and getattr(uploaded_file, 'name', ''):
        title = uploaded_file.name

    picture = Picture(
        album=album,
        title=title,
        description=form_cleaned_data.get('description', ''),
        seaweedfs_file_id=file_id,
        file_size=getattr(uploaded_file, 'size', 0) or 0,
        mime_type=getattr(uploaded_file, 'content_type', 'image/jpeg') or 'image/jpeg',
        width=width,
        height=height,
    )
    picture.save()

    tags_str = form_cleaned_data.get('tags', '')
    if tags_str:
        tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
        for tag_name in tag_names:
            picture.add_tag(tag_name)
    return picture


@login_required
def picture_upload(request, album_id):
    """Upload one or more pictures, or an archive (ZIP/TAR), to an album."""
    album = get_object_or_404(
        Album.objects.filter(
            Q(gallery__owner=request.user) | Q(gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=album_id
    )

    if request.method == 'POST':
        form = PictureUploadForm(request.POST, request.FILES, album=album)
        if form.is_valid():
            images_to_process = []

            # Collect multiple files from input name="files"
            for f in request.FILES.getlist('files'):
                if f and getattr(f, 'size', 0):
                    images_to_process.append(f)

            # Single file from input name="file" (backward compat)
            single = request.FILES.get('file')
            if single and getattr(single, 'size', 0):
                images_to_process.append(single)

            # Archive: extract images
            archive = request.FILES.get('archive')
            if archive and getattr(archive, 'size', 0):
                try:
                    for _filename, file_obj in extract_images_from_archive(archive):
                        images_to_process.append(file_obj)
                except ValueError as e:
                    messages.error(request, str(e))
                    context = {'form': form, 'album': album}
                    return render(request, 'gallery/picture_upload.html', context)
                except Exception as e:
                    messages.error(request, f'Failed to read archive: {e}')
                    context = {'form': form, 'album': album}
                    return render(request, 'gallery/picture_upload.html', context)

            if not images_to_process:
                messages.error(request, 'Please select one or more images, or upload a ZIP/TAR archive.')
                context = {'form': form, 'album': album}
                return render(request, 'gallery/picture_upload.html', context)

            created = []
            failed = []
            for uploaded_file in images_to_process:
                try:
                    picture = _process_uploaded_image(uploaded_file, album, form.cleaned_data)
                    created.append(picture)
                except Exception as e:
                    failed.append((getattr(uploaded_file, 'name', '?'), str(e)))

            if failed:
                for name, err in failed:
                    messages.error(request, f'Failed to upload {name}: {err}')
            if created:
                msg = f'{len(created)} picture(s) uploaded successfully.'
                if len(created) == 1:
                    msg = f'Picture "{created[0].title}" uploaded successfully!'
                messages.success(request, msg)
                return redirect('gallery:album_detail', pk=album.id)
            # All failed
            context = {'form': form, 'album': album}
            return render(request, 'gallery/picture_upload.html', context)
    else:
        form = PictureUploadForm(album=album)

    context = {'form': form, 'album': album}
    return render(request, 'gallery/picture_upload.html', context)


@login_required
def picture_detail(request, pk):
    """View picture details"""
    picture = get_object_or_404(
        Picture.objects.filter(
            Q(album__gallery__owner=request.user) | Q(album__gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    # Generate signed URL
    signed_url = None
    if picture.seaweedfs_file_id:
        try:
            signed = generate_signed_url(picture.seaweedfs_file_id)
            signed_url = signed['url']
        except Exception:
            pass
    
    context = {
        'picture': picture,
        'signed_url': signed_url,
    }
    return render(request, 'gallery/picture_detail.html', context)


@login_required
@require_http_methods(["POST"])
def picture_toggle_favorite(request, pk):
    """Toggle favorite status for picture (HTMX endpoint)"""
    picture = get_object_or_404(
        Picture.objects.filter(
            Q(album__gallery__owner=request.user) | Q(album__gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    
    picture.is_favorite = not picture.is_favorite
    picture.save(update_fields=['is_favorite'])
    
    # Return updated button HTML for HTMX
    button_html = render_to_string('gallery/partials/favorite_button.html', {
        'object': picture,
        'object_type': 'picture',
        'object_id': picture.id,
    }, request=request)
    
    return HttpResponse(button_html)


@login_required
@require_http_methods(["POST"])
def picture_delete(request, pk):
    """Soft-delete a single picture and redirect to album."""
    picture = get_object_or_404(
        Picture.objects.filter(
            Q(album__gallery__owner=request.user) | Q(album__gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    album_id = picture.album_id
    picture.soft_delete()
    messages.success(request, 'Picture deleted.')
    return redirect('gallery:album_detail', pk=album_id)


@login_required
@require_http_methods(["POST"])
def picture_bulk_delete(request, pk):
    """Soft-delete selected pictures in an album (bulk operation)."""
    album = get_object_or_404(
        Album.objects.filter(
            Q(gallery__owner=request.user) | Q(gallery__shared_with=request.user),
            deleted_at__isnull=True
        ),
        pk=pk
    )
    ids = request.POST.getlist('ids')
    if not ids:
        messages.warning(request, 'No pictures selected.')
        return redirect('gallery:album_detail', pk=pk)
    # Restrict to pictures in this album and not already deleted
    to_delete = album.pictures.filter(
        pk__in=ids,
        deleted_at__isnull=True
    )
    count = to_delete.count()
    for picture in to_delete:
        picture.soft_delete()
    if count == 1:
        messages.success(request, '1 picture deleted.')
    else:
        messages.success(request, f'{count} pictures deleted.')
    return redirect('gallery:album_detail', pk=pk)
