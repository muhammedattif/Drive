from django.contrib import admin
from uploader.models import Folder, File, Trash, FilePrivacy, Link
# Register your models here.

admin.site.register(Folder)
admin.site.register(File)
admin.site.register(Link)
admin.site.register(Trash)
admin.site.register(FilePrivacy)
