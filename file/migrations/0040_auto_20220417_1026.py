# Generated by Django 3.2.7 on 2022-04-17 08:26

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('file', '0039_auto_20220417_0858'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sharedobject',
            old_name='object_id',
            new_name='content_id',
        ),
        migrations.RenameField(
            model_name='sharedobject',
            old_name='object_type',
            new_name='content_type',
        ),
        migrations.AlterUniqueTogether(
            name='sharedobject',
            unique_together={('shared_by', 'content_type', 'content_id', 'shared_with')},
        ),
    ]
