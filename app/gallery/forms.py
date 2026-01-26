"""
Django forms for Gallery app
"""
from django import forms
from .models import Gallery, Album, Picture


class GalleryForm(forms.ModelForm):
    """Form for creating/editing Gallery"""
    tags = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas",
        widget=forms.TextInput(attrs={'placeholder': 'vacation, beach, summer'})
    )
    
    class Meta:
        model = Gallery
        fields = ['name', 'description', 'gallery_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'gallery_type': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-populate tags for editing
            self.fields['tags'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
    
    def save(self, commit=True):
        gallery = super().save(commit=commit)
        
        # Handle tags
        tags_str = self.cleaned_data.get('tags', '')
        if tags_str:
            tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            gallery.set_tags(tag_names)
        elif commit:
            # Clear tags if empty
            gallery.tags.clear()
        
        return gallery


class AlbumForm(forms.ModelForm):
    """Form for creating/editing Album"""
    tags = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas",
        widget=forms.TextInput(attrs={'placeholder': 'summer, beach, 2024'})
    )
    
    class Meta:
        model = Album
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.gallery = kwargs.pop('gallery', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-populate tags for editing
            self.fields['tags'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
    
    def save(self, commit=True):
        album = super().save(commit=False)
        if self.gallery:
            album.gallery = self.gallery
        if commit:
            album.save()
        
        # Handle tags
        tags_str = self.cleaned_data.get('tags', '')
        if tags_str:
            tag_names = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            album.set_tags(tag_names)
        elif commit:
            # Clear tags if empty
            album.tags.clear()
        
        return album


class PictureUploadForm(forms.ModelForm):
    """Form for uploading pictures"""
    file = forms.ImageField(
        required=True,
        help_text="Upload image file (JPG, PNG, HEIC)"
    )
    tags = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas",
        widget=forms.TextInput(attrs={'placeholder': 'sunset, beach, vacation'})
    )
    
    class Meta:
        model = Picture
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.album = kwargs.pop('album', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        # This form is mainly for file upload
        # Actual saving will be handled in the view after processing
        picture = super().save(commit=False)
        if self.album:
            picture.album = self.album
        return picture
