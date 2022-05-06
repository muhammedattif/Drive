# Django
from django.urls import path

# Local Django
from .views import ClassifiedFilesView, DriveSettingsView

app_name = 'drive'

urlpatterns = [
    path('settings/', DriveSettingsView.as_view()),
    path('classified-files/', ClassifiedFilesView.as_view())
]
