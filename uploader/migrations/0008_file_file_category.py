# Generated by Django 3.2.7 on 2021-09-23 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0007_auto_20210923_1236'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='file_category',
            field=models.CharField(default='image', max_length=30),
            preserve_default=False,
        ),
    ]
