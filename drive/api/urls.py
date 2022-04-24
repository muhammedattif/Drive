from django.urls import path
from .views import DriveSettingsView, ClassifiedFilesView

app_name = 'drive'

urlpatterns = [
    path('settings/', DriveSettingsView.as_view()),
    path('classified-files/', ClassifiedFilesView.as_view())
]
