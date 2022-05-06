# Django
from django.contrib import admin

# Activities App
from activity.models import Activity


class ActivityConfig(admin.ModelAdmin):
    model = Activity

    list_filter = ('user', 'activity_type', 'content_type')
    list_display = ('user', 'activity_type', 'content_type')

admin.site.register(Activity, ActivityConfig)
