from django.contrib import admin
from file.models import File, FileQuality, MediaFileProperties, VideoSubtitle, FilePrivacy, Trash, SharedFile, SharedFilePermission, FileSharingBlockList
from nested_inline.admin import NestedStackedInline, NestedModelAdmin

class FilePrivacyInline(NestedStackedInline):
    model = FilePrivacy
    can_delete = False
    verbose_name_plural = 'File Privacy'
    fk_name = 'file'

class FileConfig(NestedModelAdmin):
    model = File

    list_filter = ('uploader__username', 'file_size', 'file_type', 'file_category', 'uploaded_at')
    list_display = ('uploader', 'file_size', 'file_type', 'file_category', 'uploaded_at')

    inlines = [FilePrivacyInline]

class FilePrivacyConfig(admin.ModelAdmin):
    model = FilePrivacy

    list_filter = ('file__uploader__username',)
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

class SharedFilePermissionInline(NestedStackedInline):
    model = SharedFilePermission
    can_delete = False
    verbose_name_plural = 'Permissions'
    fk_name = 'file'

class SharedFileConfig(NestedModelAdmin):
    model = SharedFile

    list_filter = ('file', 'permissions__can_view', 'permissions__can_delete', 'permissions__can_download', 'permissions__can_rename')
    list_display = ('file', 'shared_with_user')

    inlines = [SharedFilePermissionInline]

admin.site.register(SharedFile, SharedFileConfig)
admin.site.register(SharedFilePermission)

admin.site.register(FileSharingBlockList)
