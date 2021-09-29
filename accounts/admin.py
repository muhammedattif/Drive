from django.contrib import admin
from accounts.models import Account, DriveSettings
# Register your models here.

admin.site.register(Account)
admin.site.register(DriveSettings)
