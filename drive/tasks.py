import time
import subprocess
from celery import shared_task
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from django.http import HttpResponse
from django.conf import settings
import os
from accounts.models import Account
from drive.models import CompressedFile

@shared_task
def async_compress_user_files(user_id, compress_id):

    user = Account.objects.get(id=user_id)
    folder_to_compress = Path(os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(user.unique_id)))
    path_to_archive_in_model =  Path(os.path.join(settings.COMPRESS_PATH, f"{str(user.unique_id)}{'.zip'}"))

    path_to_archive_in_os = Path(
        os.path.join(settings.MEDIA_ROOT, settings.COMPRESS_PATH, f"{str(user.unique_id)}{'.zip'}"))

    with ZipFile(
            path_to_archive_in_os,
            mode="w",
            compression=ZIP_DEFLATED
    ) as zip:
        for file in folder_to_compress.rglob("*"):
            relative_path = file.relative_to(folder_to_compress)
            print(f"Packing {file} as {relative_path}")
            zip.write(file, arcname=relative_path)


    compressed_data = CompressedFile.objects.get(id=compress_id)
    compressed_data.zip = str(path_to_archive_in_model)
    compressed_data.is_compressed = True
    compressed_data.save(update_fields=['zip', 'is_compressed'])
