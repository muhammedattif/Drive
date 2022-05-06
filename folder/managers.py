# Django
from django.db import models


class FolderQuerySet(models.QuerySet):
    def annotate_sub_files_count(self):
        return self.annotate(sub_files_count=models.Count('files' ,distinct=True))

    def annotate_sub_folders_count(self):
        return self.annotate(sub_folders_count=models.Count('sub_folders', distinct=True))

    def annotate_size(self):
        return self.annotate(sub_folders_count=models.Count('sub_folders', distinct=True))

class FolderManager(models.Manager):
    def get_queryset(self):
        return FolderQuerySet(self.model, using=self._db)

    def annotate_sub_files_count(self):
        return self.get_queryset().annotate_sub_files_count()

    def annotate_sub_folders_count(self):
        return self.get_queryset().annotate_sub_folders_count()
