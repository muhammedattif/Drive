from django.contrib import admin
from file.models import File, FilePrivacy, Trash

class FilePrivacyInline(admin.StackedInline):
    model = FilePrivacy
    can_delete = False
    verbose_name_plural = 'File Privacy'
    fk_name = 'file'

class FileConfig(admin.ModelAdmin):
    model = File

    list_filter = ('uploader', 'file_size', 'file_type', 'file_category', 'uploaded_at')
    list_display = ('uploader', 'file_size', 'file_type', 'file_category', 'uploaded_at')

    inlines = (FilePrivacyInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(FileConfig, self).get_inline_instances(request, obj)

class FilePrivacyConfig(admin.ModelAdmin):
    model = FilePrivacy

    list_display = ('file', 'option')

class TrashConfig(admin.ModelAdmin):
    model = Trash

    list_filter = ('user', 'file', 'trashed_at')
    list_display = ('user', 'file', 'trashed_at')


admin.site.register(File, FileConfig)
admin.site.register(FilePrivacy, FilePrivacyConfig)
admin.site.register(Trash, TrashConfig)
