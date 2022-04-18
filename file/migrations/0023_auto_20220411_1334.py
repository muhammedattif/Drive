# Generated by Django 3.2.7 on 2022-04-11 11:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0022_sharedfile_sharedfilepermissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedFilePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_view', models.BooleanField(default=True)),
                ('can_download', models.BooleanField(default=False)),
                ('can_delete', models.BooleanField(default=False)),
                ('file', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='file.sharedfile')),
            ],
        ),
        migrations.DeleteModel(
            name='SharedFilePermissions',
        ),
    ]