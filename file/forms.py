# Django
from django.forms import ModelForm

# Local Django
from file.models import FilePrivacy


class FilePrivacyForm(ModelForm):
    class Meta:
        model = FilePrivacy
        fields = ['option']
