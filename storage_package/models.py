from django.db import models, IntegrityError
from django.conf import settings

# Storage package Model
class StoragePackage(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, unique=True)
    storage = models.FloatField(help_text="Storage in GB.", default=settings.BASIC_PACKAGE_STORAGE_LIMIT, null=False, blank=False)
    duration = models.FloatField(help_text="Duration in months.", null=True)
    price = models.FloatField(null=True)
    default = models.BooleanField(default=False, unique=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_default_package(cls):
        try:
            default_package, created = StoragePackage.objects.get_or_create(
                name=settings.BASIC_PACKAGE_NAME, storage=settings.BASIC_PACKAGE_STORAGE_LIMIT, default=True)
            return default_package.pk
        except IntegrityError:
            # in case a default package is exists and the values changed from settings file
            old_default_package = StoragePackage.objects.get(default=True)
            old_default_package.name = settings.BASIC_PACKAGE_NAME
            old_default_package.storage = settings.BASIC_PACKAGE_STORAGE_LIMIT
            old_default_package.save()

