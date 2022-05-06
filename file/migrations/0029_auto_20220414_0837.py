# Generated by Django 3.2.7 on 2022-04-14 06:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('file', '0028_auto_20220413_1040'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharedfile',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='shared_files', to='accounts.account'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='sharedfile',
            unique_together={('user', 'file', 'shared_with_user')},
        ),
    ]
