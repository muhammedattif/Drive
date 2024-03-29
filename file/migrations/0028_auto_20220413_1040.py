# Generated by Django 3.2.7 on 2022-04-13 08:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('file', '0027_alter_filesharingblocklist_users'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharedfile',
            name='file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_with', to='file.file'),
        ),
        migrations.AlterField(
            model_name='sharedfile',
            name='shared_with_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shared_with_me', to=settings.AUTH_USER_MODEL),
        ),
    ]
