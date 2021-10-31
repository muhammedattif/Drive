from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from accounts.models import Account
from drive.models import DriveSettings
from rest_framework.authtoken.models import Token


# this is a receiver for creating an auth token for the user after creating his profile
@receiver(post_save, sender=Account)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


# this receiver is for creating and initializing user drive settings after creating his profile
@receiver(post_save, sender=Account)
def create_user_drive_settings(sender, instance=None, created=False, **kwargs):
    if created:
        if instance.is_superuser:
            DriveSettings.objects.create(user=instance, unlimited_storage=True)
        else:
            DriveSettings.objects.create(user=instance)
