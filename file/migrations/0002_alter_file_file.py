# Generated by Django 3.2.7 on 2021-11-02 07:28

from django.db import migrations, models

import file.utils


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file',
            field=models.FileField(max_length=300, upload_to=file.utils.get_file_path),
        ),
    ]
