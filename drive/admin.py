from django.contrib import admin
from drive.models import DriveSettings

class DriveSettingsConfig(admin.ModelAdmin):
    model = DriveSettings

    list_filter = ('user__username', 'storage_package', 'storage_uploaded', 'unlimited_storage')
    list_display = ('user', 'storage_package', 'storage_uploaded', 'unlimited_storage')

admin.site.register(DriveSettings, DriveSettingsConfig)