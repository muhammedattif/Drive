# Generated by Django 3.2.7 on 2021-10-19 07:38

import accounts.models
from django.conf import settings
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('unique_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('email', models.EmailField(max_length=60, unique=True, verbose_name='email')),
                ('username', models.CharField(max_length=30, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()])),
                ('job_title', models.CharField(max_length=30)),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')),
                ('last_login', models.DateTimeField(auto_now=True, verbose_name='Last Login')),
                ('image', models.ImageField(blank=True, null=True, upload_to=accounts.models.get_profile_image_path)),
                ('is_admin', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, accounts.models.ResizeImageMixin),
        ),
        migrations.CreateModel(
            name='DriveSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('storage_limit', models.FloatField(default=15, help_text='Storage in GB.')),
                ('storage_uploaded', models.FloatField(default=0, help_text='Storage in GB.')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='drive_settings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'DriveSettings',
            },
        ),
    ]
