# Data migration: copy existing Picture.tags (user) and Picture.ai_tags (ai) into PictureTag

from django.db import migrations
from django.utils.text import slugify


def forwards(apps, schema_editor):
    Picture = apps.get_model('gallery', 'Picture')
    PictureTag = apps.get_model('gallery', 'PictureTag')
    Tag = apps.get_model('gallery', 'Tag')
    for picture in Picture.objects.all():
        for tag in picture.tags.all():
            PictureTag.objects.get_or_create(
                picture=picture,
                tag=tag,
                source='user',
                defaults={},
            )
        for name in (picture.ai_tags or []):
            name_normalized = name.lower().strip() if name else ''
            if not name_normalized:
                continue
            slug = slugify(name_normalized)
            tag, _ = Tag.objects.get_or_create(
                slug=slug,
                defaults={'name': name_normalized},
            )
            PictureTag.objects.get_or_create(
                picture=picture,
                tag=tag,
                source='ai',
                defaults={},
            )


def backwards(apps, schema_editor):
    PictureTag = apps.get_model('gallery', 'PictureTag')
    PictureTag.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0002_picturetag'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
