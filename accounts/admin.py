from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import Account, DriveSettings

class DriveSettingsInline(admin.StackedInline):
    model = DriveSettings
    can_delete = False
    verbose_name_plural = 'Drive Settings'
    fk_name = 'user'

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

    inlines = (DriveSettingsInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(AccountAdmin, self).get_inline_instances(request, obj)




# Register your models here.
admin.site.register(Account, AccountAdmin)
admin.site.register(DriveSettings)
