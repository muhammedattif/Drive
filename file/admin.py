from django.contrib import admin
from file.models import File, FilePrivacy, Trash

admin.site.register(File)
admin.site.register(FilePrivacy)
admin.site.register(Trash)
