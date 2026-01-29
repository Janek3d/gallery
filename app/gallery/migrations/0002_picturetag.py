# Generated manually for PictureTag through model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PictureTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(
                    choices=[('user', 'User'), ('ai', 'AI')],
                    help_text='Whether this tag was added by user or by AI (e.g. YOLO)',
                    max_length=10,
                    verbose_name='Source',
                )),
                ('picture', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tag_links',
                    to='gallery.picture',
                    verbose_name='Picture',
                )),
                ('tag', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='picture_tag_links',
                    to='gallery.tag',
                    verbose_name='Tag',
                )),
            ],
            options={
                'verbose_name': 'Picture–Tag',
                'verbose_name_plural': 'Picture–Tags',
            },
        ),
        migrations.AddConstraint(
            model_name='picturetag',
            constraint=models.UniqueConstraint(
                fields=('picture', 'tag', 'source'),
                name='gallery_picturetag_unique_picture_tag_source',
            ),
        ),
        migrations.AddIndex(
            model_name='picturetag',
            index=models.Index(fields=['picture', 'source'], name='gallery_pictag_pic_src_idx'),
        ),
    ]
