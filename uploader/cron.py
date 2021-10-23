from uploader.models import Trash
from uploader.models import Folder
from django.conf import settings
User = settings.AUTH_USER_MODEL
import logging

def delete_trashed_files():

    all_trashed_files = Trash.objects.all()
    for file in all_trashed_files:
        if file.to_be_deleted():
            file.file.delete()
