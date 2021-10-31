from django.db import models
from accounts.models import Account
from storage_package.models import StoragePackage
from django.db.models import F


# This class is for Drive Settings Model for the user
class DriveSettings(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="drive_settings")
    storage_package = models.ForeignKey(StoragePackage, default=StoragePackage.get_default_package,
                                        on_delete=models.CASCADE, related_name="package")
    storage_uploaded = models.FloatField(help_text="Storage in GB.", default=0)
    unlimited_storage = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Drive Settings"

    def __str__(self):
        return self.user.username

    def get_used_storage_percentage(self):
        """
        This function returns percentage used of user's storage
        """
        if self.unlimited_storage:
            return 0
        return (self.storage_uploaded / self.storage_package.storage) * 100

    def get_storage_limit_in_bytes(self):
        """
        This function returns user's storage in bytes
        """
        if self.unlimited_storage:
            return 0
        return self.storage_package.storage * 1073741824

    def get_storage_uploaded_in_bytes(self):
        """
        This function returns user's used storage in bytes
        """
        return self.storage_uploaded * 1073741824

    def add_storage_uploaded(self, file_size):
        """
        This function add the uploaded file size to the uploaded storage of the user
        """
        self.storage_uploaded = F('storage_uploaded') + file_size / 1073741824

    def subtract_storage_uploaded(self, file_size):
        """
        This function subtract the deleted file size from the uploaded storage of the user
        """
        self.storage_uploaded = F('storage_uploaded') - file_size / 1073741824

    def is_allowed_to_upload_files(self, files_size):
        """
        This function returns True if the user not reached his upload limit, otherwise returns False
        """
        if self.unlimited_storage:
            return True

        elif self.storage_uploaded < self.storage_package.storage:
            storage_after_upload = self.storage_uploaded + (files_size / 1073741824)
            if storage_after_upload < self.storage_package.storage:
                return True

        return False