from django.contrib import admin
from drive.models import DriveSettings, CompressedFile

class DriveSettingsConfig(admin.ModelAdmin):
    model = DriveSettings

    list_filter = ('user__username', 'storage_package', 'storage_uploaded', 'unlimited_storage')
    list_display = ('user', 'storage_package', 'storage_uploaded', 'unlimited_storage')

class CompressedFileConfig(admin.ModelAdmin):
    model = CompressedFile

    list_filter = ('user__username', 'compressed_at')
    list_display = ('user', 'compressed_at', 'is_compressed')

admin.site.register(DriveSettings, DriveSettingsConfig)
admin.site.register(CompressedFile, CompressedFileConfig)