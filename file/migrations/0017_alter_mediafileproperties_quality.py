# Generated by Django 3.2.7 on 2022-03-16 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0016_auto_20220316_1357'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediafileproperties',
            name='quality',
            field=models.CharField(choices=[('144p', '144p'), ('240p', '240p'), ('480p', '480p'), ('720p', '720p'), ('1080p', '1080p')], default='144p', max_length=100),
        ),
    ]
