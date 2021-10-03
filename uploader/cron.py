

from uploader.models import Trash
from uploader.models import Folder
from django.conf import settings
User = settings.AUTH_USER_MODEL
import logging
logger = logging.getLogger(__name__)

def delete_trashed_files():
    logger.info("hello")

    folder = Folder.objects.get(pk=1)
    folder.name = "ahmed"
    folder.save()
    # all_trashed_files = Trash.objects.all()
    # for file in all_trashed_files:
    #     if file.to_be_deleted():
    #         file.delete()
