from file.models import File, FilePrivacy, MediaFileProperties, SharedObject, SharedObjectPermission
from activity.models import Activity
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os
from file.utils import detect_quality
from django.db import transaction

# This function is used as a decorator for the signals
# to ensure that all data has been committed within
# the transaction for Transactions
def on_transaction_commit(func):
    def inner(*args, **kwargs):
        transaction.on_commit(lambda: func(*args, **kwargs))
    return inner

# This function is for Creating Privacy object for a file
@receiver(post_save, sender=File)
def create_file_privacy(sender, instance=None, created=False, **kwargs):
    if created:
        FilePrivacy.objects.create(file=instance)

# This function is for Creating Media file Props
@receiver(post_save, sender=File)
def create_media_file_props(sender, instance=None, created=False, **kwargs):
    if created and instance.category == 'media':
        media_file_quality = detect_quality(instance.file.path)
        MediaFileProperties.objects.create(media_file=instance, quality=media_file_quality)

# This function is for recording activity of a file
@receiver(post_save, sender=File)
def record_activity_on_upload_file(sender, instance=None, created=False, **kwargs):
    if created:
        instance.activities.create(
            activity_type=Activity.UPLOAD_FILE,
            user=instance.user,
            object_name=instance.name
        )


# This function is for recording activity of a file
@receiver(post_delete, sender=File)
def record_activity_on_delete_file(sender, instance, **kwargs):
    instance.activities.create(
        activity_type=Activity.DELETE_FILE,
        user=instance.user,
        object_name=instance.name
    )


# This function is for cleaning file name before uploading
@receiver(post_save, sender=File)
def add_storage_uploaded(sender, instance=None, created=False, **kwargs):
    if created:
        file_size = instance.size
        instance.user.drive_settings.add_storage_uploaded(file_size)
        instance.user.drive_settings.save()


@receiver(post_delete, sender=File)
def subtract_storage_uploaded(sender, instance, **kwargs):
    file_size = instance.size
    instance.user.drive_settings.subtract_storage_uploaded(file_size)
    instance.user.drive_settings.save()


# This function is for cleaning file name before uploading
@receiver(post_save, sender=File)
def clean_file_name(sender, instance=None, created=False, **kwargs):
    if created:
        instance.name = os.path.basename(instance.file.path)
        instance.save()


@receiver(post_delete, sender=File)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `File` object is deleted.
    """
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)


# This function is for setting Shares File Default Permissions if not created by the user
@receiver(post_save, sender=SharedObject)
@on_transaction_commit
def create_shared_file_permissions(sender, instance=None, created=False, **kwargs):
    if created and not hasattr(instance, 'permissions'):
        SharedObjectPermission.objects.create(file=instance)
