# Generated by Django 3.2.7 on 2022-04-14 07:30

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('file', '0029_auto_20220414_0837'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sharedfile',
            old_name='user',
            new_name='shared_by',
        ),
        migrations.RenameField(
            model_name='sharedfile',
            old_name='shared_with_user',
            new_name='shared_with',
        ),
        migrations.AlterUniqueTogether(
            name='sharedfile',
            unique_together={('shared_by', 'file', 'shared_with')},
        ),
    ]
