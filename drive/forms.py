# Django
from django.forms import ModelForm

# Local Django
from .models import DriveSettings


class PrivacySettingsForm(ModelForm):
    class Meta:
        model = DriveSettings
        fields = ['default_upload_privacy']
