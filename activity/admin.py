from django.contrib import admin
from activity.models import Activity
from django.contrib.auth.admin import UserAdmin


class ActivityConfig(admin.ModelAdmin):
    model = Activity

    list_filter = ('user', 'activity_type', 'content_type')
    list_display = ('user', 'activity_type', 'content_type')

admin.site.register(Activity, ActivityConfig)
