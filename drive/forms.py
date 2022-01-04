from .models import DriveSettings
from django.forms import ModelForm


class PrivacySettingsForm(ModelForm):
    class Meta:
        model = DriveSettings
        fields = ['default_upload_privacy']
