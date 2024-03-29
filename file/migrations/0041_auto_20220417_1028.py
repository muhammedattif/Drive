# Generated by Django 3.2.7 on 2022-04-17 08:28

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('file', '0040_auto_20220417_1026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sharedobject',
            old_name='content_id',
            new_name='object_id',
        ),
        migrations.AlterUniqueTogether(
            name='sharedobject',
            unique_together={('shared_by', 'content_type', 'object_id', 'shared_with')},
        ),
    ]
