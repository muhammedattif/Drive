# Generated by Django 3.2.7 on 2021-11-02 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('folder', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='folder',
            name='name',
            field=models.CharField(default='New Folder', max_length=60),
        ),
    ]
