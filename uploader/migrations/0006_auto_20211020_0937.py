# Generated by Django 3.2.7 on 2021-10-20 07:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uploader', '0005_auto_20211017_0810'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='link',
            field=models.CharField(default='sgfgfdgd', max_length=255, unique=True),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Link',
        ),
    ]
