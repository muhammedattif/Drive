# Generated by Django 3.2.7 on 2022-04-11 08:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0018_auto_20220329_1319'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='file',
            options={'ordering': ('-uploaded_at',), 'permissions': (('can_download_file', 'Can Download File'), ('can_convert_media_files', 'Can Convert Media Files'), ('can_stream_media_files', 'Can Stream Media Files'))},
        ),
    ]