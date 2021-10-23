from django.contrib import admin
from accounts.models import Account, DriveSettings
# Register your models here.
class AccountAdmin(admin.ModelAdmin):
    fields = (
    'email',
    'username',
    'job_title',
    'image',
    'is_active',
    'is_staff',
    'is_superuser',
    'groups',
    'user_permissions'
    )

admin.site.register(Account, AccountAdmin)
admin.site.register(DriveSettings)
