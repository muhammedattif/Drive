# Generated by Django 3.2.7 on 2022-03-07 05:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0008_filequality_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filequality',
            name='converted_file',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='file.file'),
        ),
    ]
