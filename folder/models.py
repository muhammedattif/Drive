from django.db import models
from activity.models import Activity
from accounts.models import Account
from django.contrib.contenttypes.fields import GenericRelation
import uuid


# Folder Model
class Folder(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="folders")
    name = models.CharField(default="New Folder", max_length=30)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Date Created", auto_now_add=True)
    activities = GenericRelation(Activity)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.username}-{self.name}'

    def get_absolute_url(self):
        return f'/folder/{self.unique_id}'

    def get_files_count(self):
        return self.files.filter(trash=None).count()

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

    # This function id to return folder tree as objects [<folder_obj2>, <folder_obj2>, <folder_obj3>]
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
