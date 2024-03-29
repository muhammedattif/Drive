# Generated by Django 3.2.7 on 2021-10-31 10:28

import uuid

import django.contrib.auth.validators
from django.db import migrations, models

import accounts.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('unique_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('email', models.EmailField(max_length=60, unique=True, verbose_name='email')),
                ('username', models.CharField(max_length=30, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()])),
                ('job_title', models.CharField(max_length=30)),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='Date Joined')),
                ('last_login', models.DateTimeField(auto_now=True, verbose_name='Last Login')),
                ('image', models.ImageField(blank=True, null=True, upload_to=accounts.models.get_profile_image_path)),
                ('is_active', models.BooleanField(default=True, verbose_name='Active status')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff status')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model, accounts.models.ResizeImageMixin),
        ),
    ]
