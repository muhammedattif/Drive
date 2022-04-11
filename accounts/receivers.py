from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from accounts.models import Account
from drive.models import DriveSettings
from rest_framework.authtoken.models import Token
from django.db.models.signals import m2m_changed
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

# A workaround to add user to a group
@receiver(post_save, sender=Account)
def add_user_to_group(sender, instance, **kwargs):
    if instance.actions_type == 'allow_all':
        group, created = Group.objects.get_or_create(name='Allow all resources')
        if created:
            permissions = Permission.objects.filter(
                Q(codename='can_erase_account_data') |
                Q(codename='can_compress_account_data') |
                Q(codename='delete_file') |
                Q(codename='can_add_files_to_trash') |
                Q(codename='can_download_folder') |
                Q(codename='can_rename_folder') |
                Q(codename='delete_folder') |
                Q(codename='can_stream_media_files') |
                Q(codename='can_download_file') |
                Q(codename='can_convert_media_files') |
                Q(codename='can_stream_media_files')
            )

            group.permissions.add(*permissions)
        instance.groups.add(group)

# @receiver(m2m_changed, sender=Account.groups.through)
# def sync_user_to_group(instance, action, **kwargs):
#     print(2)
#     if action == 'post_add' and not instance.is_superuser:
#         if instance.actions_type == 'allow_all':
#             group, created = Group.objects.get_or_create(name='Allow all resources')
#             if created:
#                 permissions = Permission.objects.filter(
#                     Q(codename='can_erase_data') |
#                     Q(codename='can_compress_account_data') |
#                     Q(codename='delete_file') |
#                     Q(codename='delete_folder')
#                 )
#
#                 group.permissions.add(*permissions)
#             instance.groups.add(group)
#             return 1

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
