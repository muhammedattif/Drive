from django.contrib import admin
from .models import StoragePackage

class StoragePackageConfig(admin.ModelAdmin):
    model = StoragePackage

    list_filter = ('storage', 'duration', 'price', 'default')
    list_display = ('name', 'storage', 'duration', 'price', 'default')

admin.site.register(StoragePackage, StoragePackageConfig)
