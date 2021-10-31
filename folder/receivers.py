from folder.models import Folder
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from activity.models import Activity
from django.dispatch import receiver
import os


# This receiver is to create folder dir in physical storage
@receiver(post_save, sender=Folder)
def create_folder_dir(sender, instance=None, created=False, **kwargs):
    if created:
        if instance.parent_folder:
            folder_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(instance.user.unique_id),
                instance.parent_folder.get_folder_tree_as_dirs(),
                instance.name)
        else:
            folder_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(instance.user.unique_id),
                instance.name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)


# This receiver is to record user activity
@receiver(post_save, sender=Folder)
def record_activity_on_creating_folder(sender, instance=None, created=False, **kwargs):
    if created:
        instance.activities.create(
            activity_type=Activity.CREATE_FOLDER,
            user=instance.user,
            object_name=instance.name
        )


# This function is for recording activity of folder
@receiver(post_delete, sender=Folder)
def record_activity_on_deleting_folder(sender, instance, **kwargs):
    instance.activities.create(
        activity_type=Activity.DELETE_FOLDER,
        user=instance.user,
        object_name=instance.name
    )
