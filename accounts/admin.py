from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import Account
from drive.models import DriveSettings

class DriveSettingsInline(admin.StackedInline):
    model = DriveSettings
    can_delete = False
    verbose_name_plural = 'Drive Settings'
    fk_name = 'user'

class AccountAdmin(UserAdmin):
    model = Account

    list_filter = ('email', 'username', 'is_active', 'is_staff')
    ordering = ('-date_joined',)
    list_display = ('email', 'username',
                    'is_active', 'is_staff')

    inlines = (DriveSettingsInline, )

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(AccountAdmin, self).get_inline_instances(request, obj)

    fieldsets = (
        ("User Information", {'fields': ('email', 'username', 'job_title', 'image')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )




# Register your models here.
admin.site.register(Account, AccountAdmin)
