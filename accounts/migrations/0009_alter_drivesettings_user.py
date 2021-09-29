# Generated by Django 3.2.7 on 2021-09-29 14:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_auto_20210929_1608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drivesettings',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='drive_settings', to=settings.AUTH_USER_MODEL),
        ),
    ]
