from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
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
        default_package, created = StoragePackage.objects.get_or_create(
            name='basic', storage=settings.BASIC_PACKAGE_STORAGE_LIMIT, default=True)
        return default_package.pk
