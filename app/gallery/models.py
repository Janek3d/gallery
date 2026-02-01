"""
Gallery models: Gallery, Album, Picture, Tag
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.utils.text import slugify

User = get_user_model()


class Tag(models.Model):
    """Shared Tag model for Gallery, Album, and Picture"""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Tag Name',
        help_text='Tag name (case-insensitive, normalized)'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Tag Slug',
        help_text='URL-friendly tag identifier'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Usage Count',
        help_text='Number of times this tag is used across all objects'
    )
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from name"""
        if not self.slug:
            self.slug = slugify(self.name)
        # Normalize name to lowercase for consistency
        self.name = self.name.lower().strip()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_or_create_tag(cls, name):
        """Get or create a tag by name (case-insensitive)"""
        name_normalized = name.lower().strip()
        slug = slugify(name_normalized)
        tag, created = cls.objects.get_or_create(
            slug=slug,
            defaults={'name': name_normalized}
        )
        return tag, created
    
    def increment_usage(self):
        """Increment usage count"""
        Tag.objects.filter(pk=self.pk).update(usage_count=models.F('usage_count') + 1)
        self.refresh_from_db()
    
    def decrement_usage(self):
        """Decrement usage count"""
        Tag.objects.filter(pk=self.pk, usage_count__gt=0).update(usage_count=models.F('usage_count') - 1)
        self.refresh_from_db()


class PictureTag(models.Model):
    """Through model for Picture–Tag with source: user-added, AI-added, or EXIF-derived."""
    class Source(models.TextChoices):
        USER = 'user', 'User'
        AI = 'ai', 'AI'
        EXIF = 'exif', 'EXIF'

    picture = models.ForeignKey(
        'Picture',
        on_delete=models.CASCADE,
        related_name='tag_links',
        verbose_name='Picture',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='picture_tag_links',
        verbose_name='Tag',
    )
    source = models.CharField(
        max_length=10,
        choices=Source.choices,
        verbose_name='Source',
        help_text='Whether this tag was added by user, AI (e.g. YOLO), or EXIF extraction',
    )

    class Meta:
        verbose_name = 'Picture–Tag'
        verbose_name_plural = 'Picture–Tags'
        constraints = [
            models.UniqueConstraint(
                fields=['picture', 'tag', 'source'],
                name='gallery_picturetag_unique_picture_tag_source',
            ),
        ]
        indexes = [
            models.Index(fields=['picture', 'source']),
        ]

    def __str__(self):
        return f'{self.picture_id} – {self.tag.name} ({self.source})'


class Gallery(models.Model):
    """Gallery model - top level container for albums"""
    
    class GalleryType(models.TextChoices):
        PRIVATE = 'private', 'Private'
        PUBLIC = 'public', 'Public'
    
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='galleries',
        verbose_name='Owner'
    )
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(1)],
        verbose_name='Gallery Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    gallery_type = models.CharField(
        max_length=10,
        choices=GalleryType.choices,
        default=GalleryType.PRIVATE,
        verbose_name='Gallery Type'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='galleries',
        blank=True,
        verbose_name='Tags',
        help_text='Tags for the gallery'
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name='Is Favorite'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deleted At'
    )
    
    # Shared access
    shared_with = models.ManyToManyField(
        User,
        through='GalleryShare',
        related_name='shared_galleries',
        blank=True,
        verbose_name='Shared With'
    )
    
    class Meta:
        verbose_name = 'Gallery'
        verbose_name_plural = 'Galleries'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'gallery_type']),
            models.Index(fields=['deleted_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.owner.username})"
    
    @property
    def is_deleted(self):
        """Check if gallery is soft deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Soft delete the gallery"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    def restore(self):
        """Restore soft deleted gallery"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    def add_tag(self, tag_name):
        """Add a tag to the gallery"""
        tag, _ = Tag.get_or_create_tag(tag_name)
        if tag not in self.tags.all():
            self.tags.add(tag)
            tag.increment_usage()
    
    def remove_tag(self, tag_name):
        """Remove a tag from the gallery"""
        try:
            tag = Tag.objects.get(slug=slugify(tag_name.lower().strip()))
            if tag in self.tags.all():
                self.tags.remove(tag)
                tag.decrement_usage()
        except Tag.DoesNotExist:
            raise
    
    @classmethod
    def search_by_tags(cls, tag_names, user=None):
        """Search galleries by tags"""
        queryset = cls.objects.filter(deleted_at__isnull=True)
        if user:
            queryset = queryset.filter(owner=user)
        
        if tag_names:
            queryset = queryset.filter(tags__name__in=tag_names).distinct()
        
        return queryset
    
    def set_tags(self, tag_names):
        """Set tags from a list of tag names"""
        # Remove old tags
        for tag in self.tags.all():
            self.tags.remove(tag)
            tag.decrement_usage()
        
        # Add new tags
        for tag_name in tag_names:
            self.add_tag(tag_name)


class GalleryShare(models.Model):
    """Through model for sharing galleries with users"""
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='shares'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gallery_shares'
    )
    shared_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Shared At'
    )
    can_edit = models.BooleanField(
        default=False,
        verbose_name='Can Edit'
    )
    
    class Meta:
        unique_together = ['gallery', 'user']
        verbose_name = 'Gallery Share'
        verbose_name_plural = 'Gallery Shares'
        ordering = ['-shared_at']


class Album(models.Model):
    """Album model - container for pictures within a gallery"""
    
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='albums',
        verbose_name='Gallery'
    )
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(1)],
        verbose_name='Album Name'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='albums',
        blank=True,
        verbose_name='Tags',
        help_text='Tags for the album'
    )
    exif_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='EXIF metadata extracted from pictures'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deleted At'
    )
    
    class Meta:
        verbose_name = 'Album'
        verbose_name_plural = 'Albums'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gallery', 'deleted_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.gallery.name})"
    
    @property
    def is_deleted(self):
        """Check if album is soft deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Soft delete the album"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    def restore(self):
        """Restore soft deleted album"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    def update_exif_metadata(self, metadata_dict):
        """Update EXIF metadata, merging with existing"""
        if not isinstance(self.exif_metadata, dict):
            self.exif_metadata = {}
        self.exif_metadata.update(metadata_dict)
        self.save(update_fields=['exif_metadata'])
    
    def add_tag(self, tag_name):
        """Add a tag to the album"""
        tag, _ = Tag.get_or_create_tag(tag_name)
        if tag not in self.tags.all():
            self.tags.add(tag)
            tag.increment_usage()
    
    def remove_tag(self, tag_name):
        """Remove a tag from the album"""
        try:
            tag = Tag.objects.get(slug=slugify(tag_name.lower().strip()))
            if tag in self.tags.all():
                self.tags.remove(tag)
                tag.decrement_usage()
        except Tag.DoesNotExist:
            pass
    
    @classmethod
    def search_by_tags(cls, tag_names, gallery=None):
        """Search albums by tags"""
        queryset = cls.objects.filter(deleted_at__isnull=True)
        if gallery:
            queryset = queryset.filter(gallery=gallery)
        
        if tag_names:
            queryset = queryset.filter(tags__name__in=tag_names).distinct()
        
        return queryset
    
    def set_tags(self, tag_names):
        """Set tags from a list of tag names"""
        # Remove old tags
        for tag in self.tags.all():
            self.tags.remove(tag)
            tag.decrement_usage()
        
        # Add new tags
        for tag_name in tag_names:
            self.add_tag(tag_name)


class Picture(models.Model):
    """Picture model - individual photo stored on SeaweedFS"""
    
    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='pictures',
        verbose_name='Album'
    )
    title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Title'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Description'
    )
    
    # SeaweedFS storage
    seaweedfs_file_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='SeaweedFS File ID',
        help_text='File ID from SeaweedFS'
    )
    seaweedfs_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='SeaweedFS URL',
        help_text='Full URL to file in SeaweedFS'
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='File Size (bytes)'
    )
    mime_type = models.CharField(
        max_length=100,
        default='image/jpeg',
        verbose_name='MIME Type'
    )
    width = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Width (px)'
    )
    height = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Height (px)'
    )
    
    # AI-generated metadata (ocr_text; AI tags are in tags M2M via PictureTag.source='ai')
    ocr_text = models.TextField(
        blank=True,
        help_text='Text extracted by OCR (PaddleOCR)'
    )
    exif_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='EXIF metadata from the image'
    )
    
    # Tags (user and AI) via through model PictureTag with source='user' or 'ai'
    tags = models.ManyToManyField(
        Tag,
        through=PictureTag,
        related_name='pictures',
        blank=True,
        verbose_name='Tags',
        help_text='Tags (user and AI); use tag_links with source to distinguish',
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name='Is Favorite'
    )
    
    # Timestamps
    taken_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Taken At',
        help_text='Date/time when photo was taken (from EXIF)'
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Uploaded At'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated At'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Deleted At'
    )
    
    class Meta:
        verbose_name = 'Picture'
        verbose_name_plural = 'Pictures'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['album', 'deleted_at']),
            models.Index(fields=['taken_at']),
            models.Index(fields=['is_favorite']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Untitled'} ({self.album.name})"
    
    @property
    def is_deleted(self):
        """Check if picture is soft deleted"""
        return self.deleted_at is not None
    
    def soft_delete(self):
        """Soft delete the picture"""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    def restore(self):
        """Restore soft deleted picture"""
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    @property
    def user_tags(self):
        """Tag queryset for user-added tags (source='user')."""
        return Tag.objects.filter(
            picture_tag_links__picture=self,
            picture_tag_links__source=PictureTag.Source.USER,
        ).distinct()

    @property
    def ai_tags(self):
        """Tag queryset for AI-added tags (source='ai')."""
        return Tag.objects.filter(
            picture_tag_links__picture=self,
            picture_tag_links__source=PictureTag.Source.AI,
        ).distinct()

    @property
    def exif_tags(self):
        """Tag queryset for EXIF-derived tags (source='exif')."""
        return Tag.objects.filter(
            picture_tag_links__picture=self,
            picture_tag_links__source=PictureTag.Source.EXIF,
        ).distinct()

    @property
    def all_tags(self):
        """List of all tag names (user + AI)."""
        names = list(self.tags.values_list('name', flat=True))
        return list(dict.fromkeys(names))  # preserve order, dedupe

    def add_tag(self, tag_name):
        """Add a user-defined tag to the picture (source='user')."""
        tag, _ = Tag.get_or_create_tag(tag_name)
        _, created = PictureTag.objects.get_or_create(
            picture=self,
            tag=tag,
            source=PictureTag.Source.USER,
            defaults={},
        )
        if created:
            tag.increment_usage()

    def remove_tag(self, tag_name):
        """Remove a user-defined tag from the picture."""
        try:
            tag = Tag.objects.get(slug=slugify(tag_name.lower().strip()))
            deleted = PictureTag.objects.filter(
                picture=self,
                tag=tag,
                source=PictureTag.Source.USER,
            ).delete()
            if deleted[0]:
                tag.decrement_usage()
        except Tag.DoesNotExist:
            pass

    @classmethod
    def search_by_tags(cls, tag_names, album=None, user=None):
        """Search pictures by tags (any source)."""
        queryset = cls.objects.filter(deleted_at__isnull=True)
        if album:
            queryset = queryset.filter(album=album)
        if user:
            queryset = queryset.filter(album__gallery__owner=user)
        if tag_names:
            queryset = queryset.filter(tags__name__in=tag_names).distinct()
        return queryset

    def set_tags(self, tag_names):
        """Set user tags from a list of tag names (replaces existing user tags)."""
        # Remove existing user tag links and decrement usage
        for pt in PictureTag.objects.filter(picture=self, source=PictureTag.Source.USER).select_related('tag'):
            pt.tag.decrement_usage()
        PictureTag.objects.filter(picture=self, source=PictureTag.Source.USER).delete()
        # Add new user tags
        for tag_name in tag_names:
            self.add_tag(tag_name)

    def add_ai_tag(self, tag_name):
        """Add an AI-generated tag (source='ai')."""
        tag, _ = Tag.get_or_create_tag(tag_name)
        created = PictureTag.objects.get_or_create(
            picture=self,
            tag=tag,
            source=PictureTag.Source.AI,
            defaults={},
        )[1]
        if created:
            tag.increment_usage()

    def remove_ai_tag(self, tag_name):
        """Remove an AI-generated tag."""
        try:
            tag = Tag.objects.get(slug=slugify(tag_name.lower().strip()))
            deleted = PictureTag.objects.filter(
                picture=self,
                tag=tag,
                source=PictureTag.Source.AI,
            ).delete()
            if deleted[0]:
                tag.decrement_usage()
        except Tag.DoesNotExist:
            pass

    def set_ai_tags(self, tag_names):
        """Replace AI tags with the given list of tag names (e.g. from YOLO)."""
        for pt in PictureTag.objects.filter(picture=self, source=PictureTag.Source.AI).select_related('tag'):
            pt.tag.decrement_usage()
        PictureTag.objects.filter(picture=self, source=PictureTag.Source.AI).delete()
        for tag_name in (tag_names or []):
            name = (tag_name or '').strip()
            if name:
                self.add_ai_tag(name)

    def add_exif_tag(self, tag_name):
        """Add an EXIF-derived tag (source='exif')."""
        tag, _ = Tag.get_or_create_tag(tag_name)
        created = PictureTag.objects.get_or_create(
            picture=self,
            tag=tag,
            source=PictureTag.Source.EXIF,
            defaults={},
        )[1]
        if created:
            tag.increment_usage()

    def set_exif_tags(self, tag_names):
        """Replace EXIF tags with the given list of tag names (e.g. from EXIF extraction)."""
        for pt in PictureTag.objects.filter(picture=self, source=PictureTag.Source.EXIF).select_related('tag'):
            pt.tag.decrement_usage()
        PictureTag.objects.filter(picture=self, source=PictureTag.Source.EXIF).delete()
        for tag_name in (tag_names or []):
            name = (tag_name or '').strip()
            if name:
                self.add_exif_tag(name)
