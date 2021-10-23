from django.db import models
from django.conf import settings

# Storage package Model
class StoragePackage(models.Model):
    name = models.CharField(max_length=30, null=False, blank=False, unique=True)
    storage = models.FloatField(help_text="Storage in GB.", default=settings.MAX_STORAGE_LIMIT, null=False, blank=False)
    duration = models.FloatField(help_text="Storage in GB.", null=False, blank=False)
    price = models.FloatField(null=False, blank=False)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.name
