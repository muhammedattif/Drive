from file.models import FilePrivacy
from django.forms import ModelForm


class FilePrivacyForm(ModelForm):
    class Meta:
        model = FilePrivacy
        fields = ['option']
