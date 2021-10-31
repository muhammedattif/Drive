from file.models import File, FilePrivacy
from activity.models import Activity
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import os


# This function is for Creating Privacy object for a file
@receiver(post_save, sender=File)
def create_file_privacy(sender, instance=None, created=False, **kwargs):
    if created:
        FilePrivacy.objects.create(file=instance)


# This function is for recording activity of a file
@receiver(post_save, sender=File)
def record_activity_on_upload_file(sender, instance=None, created=False, **kwargs):
    if created:
        instance.activities.create(
            activity_type=Activity.UPLOAD_FILE,
            user=instance.uploader,
            object_name=instance.file_name
        )


# This function is for recording activity of a file
@receiver(post_delete, sender=File)
def record_activity_on_delete_file(sender, instance, **kwargs):
    instance.activities.create(
        activity_type=Activity.DELETE_FILE,
        user=instance.uploader,
        object_name=instance.file_name
    )


# This function is for cleaning file name before uploading
@receiver(post_save, sender=File)
def add_storage_uploaded(sender, instance=None, created=False, **kwargs):
    if created:
        file_size = instance.file_size
        instance.uploader.drive_settings.add_storage_uploaded(file_size)
        instance.uploader.drive_settings.save()


@receiver(post_delete, sender=File)
def subtract_storage_uploaded(sender, instance, **kwargs):
    file_size = instance.file_size
    instance.uploader.drive_settings.subtract_storage_uploaded(file_size)
    instance.uploader.drive_settings.save()


# This function is for cleaning file name before uploading
@receiver(post_save, sender=File)
def clean_file_name(sender, instance=None, created=False, **kwargs):
    if created:
        instance.file_name = os.path.basename(instance.file.url)
        instance.save()


@receiver(post_delete, sender=File)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `File` object is deleted.
    """
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)
