# Standard library
import os

# Third-party
import uuid

# Django
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Accounts App
from accounts.models import Account

# Activities App
from activity.models import Activity

# Local Django
from .managers import FolderManager


def truncate_folder_name(folder_name):
    return folder_name[0:20]

# Folder Model
class Folder(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(default="New Folder", max_length=20)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='sub_folders')
    created_at = models.DateTimeField(verbose_name="Date Created", auto_now_add=True)
    activities = GenericRelation(Activity)

    class Meta:
        ordering = ('-created_at',)
        permissions = (
            ("can_download_folder", "Can Download Folder"),
            ("can_rename_folder", "Can Rename Folder"),
            ("can_copy_folder", "Can Copy Folder"),
            ("can_move_folder", "Can Move Folder"),
        )

    objects = FolderManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            self.name = truncate_folder_name(self.name)

        if self.id:
            folder_before_save = Folder.objects.get(id=self.id)
            if folder_before_save.parent_folder != self.parent_folder or folder_before_save.name != self.name:
                changed_files = self.change_sub_files_paths(self, changed_files=[])
                if changed_files:
                    from file.models import File # isort:skip
                    File.objects.bulk_update(changed_files, ['file'])

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/folder/{self.unique_id}'

    def get_path_on_disk(self):
        return os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(self.user.unique_id), self.get_folder_tree_as_dirs())

    def get_files_count(self):
        return self.files.filter(trash=None).count()

    def change_sub_files_paths(self, folder, changed_files):

        for file in folder.files.select_related('user').all():

            base_dir = f'{settings.DRIVE_PATH}/{str(file.user.unique_id)}'

            new_path = f'{base_dir}/{folder.get_folder_tree_as_dirs()}/{file.name}'

            if str(file.file) != new_path:
                file.file.name = new_path
                changed_files.append(file)

        for folder in folder.sub_folders.prefetch_related('sub_folders', 'files').all():
            return self.change_sub_files_paths(folder, changed_files)

        if folder.sub_folders.count() == 0:
            return changed_files

    # This function id to return folder tree as objects [<folder_obj2>, <folder_obj2>, <folder_obj3>]
    # Not Used
    def recursive(self):
        folder_tree = []
        folder = self
        folder_tree.append(folder)
        while True:
            if folder.parent_folder:
                folder = folder.parent_folder
                folder_tree.append(folder)
            else:
                break
        folder_tree.reverse()
        return folder_tree

    # This function is to return folder tree as objects [<folder_obj1>, <folder_obj2>, <folder_obj3>]
    # Recursion
    def get_folder_tree(self, folder=None, folder_tree=None):

        if folder_tree is None:
            folder_tree = []
            folder = self

        if not folder.parent_folder:
            folder_tree.append(folder)
            folder_tree.reverse()
            return folder_tree
        else:
            folder_tree.append(folder)
            return self.get_folder_tree(folder.parent_folder, folder_tree)

    # This function is to return folder tree in a format like folder1/folder2/folder3
    def get_folder_tree_as_dirs(self):
        folder_tree = self.get_folder_tree()
        folder_tree = [folder.name for folder in folder_tree]
        folder_tree_dirs = '/'.join(folder_tree)
        return folder_tree_dirs

    def is_shared_with(self, user):
        from file.models import SharedObject # isort:skip
        folder_content_type = ContentType.objects.get(model='folder')

        shared_object = SharedObject.objects.filter(
        shared_with=user,
        object_id=self.id,
        content_type=folder_content_type
        ).first()

        if shared_object:
            return shared_object, True
        else:
            folder_tree = self.get_folder_tree()
            all_folders_shared_with_user = SharedObject.objects.prefetch_related('content_object__parent_folder').filter(shared_with=user, content_type=folder_content_type)
            for object in all_folders_shared_with_user:
                if object.content_object in folder_tree:
                    return object, True
            return None, False

    def is_shared_with_perm(self, user, perm):
        shared_object, is_shared = self.is_shared_with(user)
        if not is_shared:
            return None, False
        return shared_object, getattr(shared_object.permissions, perm, False)
