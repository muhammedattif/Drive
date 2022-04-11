# Generated by Django 3.2.7 on 2022-04-11 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_account_actions_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='actions_type',
            field=models.CharField(choices=[('allow_all', 'Allow all'), ('restricted', 'Restricted')], default='restricted', help_text='This option limits the user actions of the views.', max_length=15),
        ),
    ]
