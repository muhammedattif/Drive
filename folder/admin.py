# Django
from django.contrib import admin

# Local Django
from folder.models import Folder


class FolderConfig(admin.ModelAdmin):
    model = Folder

    list_filter = ('user__username', 'name', 'created_at')
    list_display = ('user', 'name', 'created_at')

admin.site.register(Folder, FolderConfig)
