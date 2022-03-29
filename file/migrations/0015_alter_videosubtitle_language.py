# Generated by Django 3.2.7 on 2022-03-09 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('file', '0014_alter_filequality_quality'),
    ]

    operations = [
        migrations.AlterField(
            model_name='videosubtitle',
            name='language',
            field=models.CharField(choices=[('en', 'English'), ('ar', 'Arabic')], default='en', max_length=100),
        ),
    ]