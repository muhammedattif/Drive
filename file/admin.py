# Django
from django.contrib import admin

# Third-party
from nested_inline.admin import NestedModelAdmin, NestedStackedInline

# Local Django
from file.models import (File, FilePrivacy, FileQuality, FileSharingBlockList,
                         MediaFileProperties, SharedObject,
                         SharedObjectPermission, Trash, VideoSubtitle)


class FilePrivacyInline(NestedStackedInline):
    model = FilePrivacy
    can_delete = False
    verbose_name_plural = 'File Privacy'
    fk_name = 'file'

class FileConfig(NestedModelAdmin):
    model = File

    list_filter = ('user__username', 'size', 'type', 'category', 'uploaded_at')
    list_display = ('user', 'file_name', 'size', 'type', 'category', 'uploaded_at')

    inlines = [FilePrivacyInline]

class FilePrivacyConfig(admin.ModelAdmin):
    model = FilePrivacy

    list_filter = ('file__user__username',)
    list_display = ('file', 'option')

class TrashConfig(admin.ModelAdmin):
    model = Trash

    list_filter = ('user__username', 'file', 'trashed_at')
    list_display = ('user', 'file', 'trashed_at')


admin.site.register(File, FileConfig)
admin.site.register(FilePrivacy, FilePrivacyConfig)
admin.site.register(FileQuality)
admin.site.register(MediaFileProperties)
admin.site.register(VideoSubtitle)
admin.site.register(Trash, TrashConfig)

class SharedObjectPermissionInline(NestedStackedInline):
    model = SharedObjectPermission
    can_delete = False
    verbose_name_plural = 'Permissions'
    fk_name = 'file'

class SharedObjectConfig(NestedModelAdmin):
    model = SharedObject

    list_filter = ('permissions__can_view', 'permissions__can_delete', 'permissions__can_download', 'permissions__can_rename')
    list_display = ('shared_by', 'content_object', 'shared_with')

    inlines = [SharedObjectPermissionInline]

admin.site.register(SharedObject, SharedObjectConfig)
admin.site.register(SharedObjectPermission)

admin.site.register(FileSharingBlockList)
