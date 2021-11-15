from django.contrib import admin
from nested_inline.admin import NestedStackedInline, NestedModelAdmin
from django.contrib.auth.admin import UserAdmin

from accounts.models import Account
from drive.models import DriveSettings

class DriveSettingsInline(NestedStackedInline):
    model = DriveSettings
    can_delete = False
    verbose_name_plural = 'Drive Settings'
    fk_name = 'user'

class AccountAdmin(UserAdmin, NestedModelAdmin):
    model = Account

    list_filter = ('email', 'username', 'is_active', 'is_staff')
    ordering = ('-date_joined',)
    list_display = ('email', 'username',
                    'is_active', 'is_staff')

    inlines = [DriveSettingsInline]

    fieldsets = (
        ("User Information", {'fields': ('email', 'username', 'job_title', 'image')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )




# Register your models here.
admin.site.register(Account, AccountAdmin)
