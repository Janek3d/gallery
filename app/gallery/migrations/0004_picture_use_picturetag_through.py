# Remove ai_tags and switch Picture.tags to use PictureTag through model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_populate_picturetag'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='picture',
            name='ai_tags',
        ),
        migrations.RemoveField(
            model_name='picture',
            name='tags',
        ),
        migrations.AddField(
            model_name='picture',
            name='tags',
            field=models.ManyToManyField(
                blank=True,
                help_text='Tags (user and AI); use tag_links with source to distinguish',
                related_name='pictures',
                through='gallery.PictureTag',
                to='gallery.tag',
                verbose_name='Tags',
            ),
        ),
    ]
