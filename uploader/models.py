from django.db import models
from django.conf import settings
from datetime import datetime
from django.contrib.sites.models import Site
from datetime import datetime, timezone
import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# image compression imports
import sys
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
# Create your models here.

User = settings.AUTH_USER_MODEL

# this function is for initializing file path
def get_file_path(self, filename):

    date = datetime.now()
    year = str(date.strftime('%Y'))
    month = str(date.strftime('%m'))
    return f'drive/{self.uploader.username}/{year}/{month}/{filename}'


# this function is for image compression
def compress_image(image, image_type):
    # Open the image and Convert it to RGB color mode
    image_temporary = Image.open(image).convert(mode='RGB', palette=Image.ADAPTIVE)

    # save image to BytesIO object
    output_io_stream = BytesIO()
    # save image to BytesIO object
    image_temporary.save(output_io_stream , format='JPEG', optimize=True)
    output_io_stream.seek(0)
    image = InMemoryUploadedFile(output_io_stream,'ImageField', "{}.{}".format(image.name.split('.')[0:-1], image.name.split('.')[-1]), image_type, sys.getsizeof(output_io_stream), None)
    return image


class File(models.Model):

    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "files")
    file = models.FileField(upload_to=get_file_path)
    file_name = models.CharField(max_length=30)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=30)
    file_category = models.CharField(max_length=30)
    uploaded_at = models.DateTimeField(verbose_name="Date Uploaded", auto_now_add=True)


    PRIVACY_CHOICES = (
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    )

    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default="public")

    class Meta:
        ordering = ('-uploaded_at',)

    def __str__(self):
        return self.file.name

    def get_url(self):
        return 'http://%s%s' % (Site.objects.get_current().domain, self.file.url)

    def is_private(self):
        return self.privacy == 'private'

    def is_public(self):
        return self.privacy == 'public'

    # this save method is used to hardcode file field
    # if the uploaded file is an image then it will be compressed
    def save(self, *args, **kwargs):
        if self.file_type.split('/')[0] == 'image' and not self.id:
            self.file = compress_image(self.file, self.file_type)
        super().save(*args, **kwargs)


# This function is for cleaning file name before uploading
@receiver(post_save, sender=File)
def clean_file_name(sender, instance=None, created=False, **kwargs):
    if created:
        instance.file_name = os.path.basename(instance.file.url)
        instance.save()

@receiver(post_delete, sender=File)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem
    when corresponding `File` object is deleted.
    """
    if instance.file and os.path.isfile(instance.file.path):
            os.remove(instance.file.path)

class Trash(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trashed_files")
    file = models.OneToOneField(File, on_delete=models.CASCADE, default=1)
    trashed_at = models.DateTimeField(verbose_name="Date Trashed", auto_now_add=True)

    def __str__(self):
          return f'{self.user.username}-{self.file.file_name}-Trash'

    # this function is buit the remainig dayes for a file to be delated
    def remaining_days(self):

        current_date = datetime.now(timezone.utc)
        delete_after_n_days = settings.TRASH_DAYS
        delta = current_date - self.trashed_at
        remaining_days = delete_after_n_days - delta.days
        if remaining_days < 0:
            return 0
        return remaining_days

    # this function is to check if the file have to be deleted
    def to_be_deleted(self):
        remaining_days = self.remaining_days()
        if remaining_days <= 0:
            return True
        return False
