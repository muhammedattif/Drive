from django.db import models
from django.conf import settings
from datetime import datetime
from django.contrib.sites.models import Site
from datetime import datetime, timezone
import os
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from django_clamd.validators import validate_file_infection


# image compression imports
import sys
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
# Create your models here.
import random
from string import digits, ascii_uppercase

User = settings.AUTH_USER_MODEL



legals = digits + ascii_uppercase
def rand_link(length, char_set=legals):

    link = ''
    for _ in range(length): link += random.choice(char_set)
    return link


# this function is for initializing file path
def get_file_path(self, filename):

    date = datetime.now()
    year = str(date.strftime('%Y'))
    month = str(date.strftime('%m'))
    day = str(date.strftime('%d'))
    return f'{settings.DRIVE_PATH}/{self.uploader.username}/{year}/{month}/{day}/{filename}'


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



class Folder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "folders")
    name = models.CharField(default="New Folder", max_length=30)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Date Created", auto_now_add=True)


    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.username}-{self.name}'

    def get_folder_tree(self):
        folder_tree = []
        folder = self
        folder_tree.append(folder)
        while True:
            if folder.parent_folder:
                folder = folder.parent_folder
                folder_tree.append(folder)
            else:
                break
        folder_tree.reverse()
        return folder_tree


class File(models.Model):
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "files")
    file = models.FileField(upload_to=get_file_path, validators=[validate_file_infection])
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=30)
    file_category = models.CharField(max_length=30)
    uploaded_at = models.DateTimeField(verbose_name="Date Uploaded", auto_now_add=True)
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files", null=True, blank=True)


    class Meta:
        ordering = ('-uploaded_at',)

    def __str__(self):
        return self.file.name

    def get_url(self):
        return f'{settings.SITE_DOMAIN}{self.file.url}'

    def is_private(self):
        return self.privacy.option == 'private'

    def is_public(self):
        return self.privacy.option == 'public'

    # this save method is used to hardcode file field
    # if the uploaded file is an image then it will be compressed
    def save(self, *args, **kwargs):
        if (self.file_type.split('/')[1].lower() == 'jpeg' or self.file_type.split('/')[1].lower() == 'jpg' or self.file_type.split('/')[1].lower() == 'png') and not self.id:
            self.file = compress_image(self.file, self.file_type)
            self.file_size = self.file.size
        super().save(*args, **kwargs)

# This function is for Creating Privacy object for a file
@receiver(post_save, sender=File)
def create_file_privacy(sender, instance=None, created=False, **kwargs):
    if created:
        FilePrivacy.objects.create(file=instance)

# This function is for cleaning file name before uploading
@receiver(post_save, sender=File)
def add_storage_uploaded(sender, instance=None, created=False, **kwargs):
    if created:
        file_size = instance.file_size
        instance.uploader.drive_settings.add_storage_uploaded(file_size)
        instance.uploader.drive_settings.save()

@receiver(post_delete, sender=File)
def subtract_storage_uploaded(sender, instance, **kwargs):

    file_size = instance.file_size
    instance.uploader.drive_settings.subtract_storage_uploaded(file_size)
    instance.uploader.drive_settings.save()

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

class FilePrivacy(models.Model):
    PRIVACY_CHOICES = (
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    )
    file = models.OneToOneField(File, on_delete=models.CASCADE, default=1, related_name='privacy')
    option = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default="private")
    shared_with = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return f'{self.file.uploader.username}-{self.file.parent_folder}-{self.file.file_name}'



class Trash(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trashed_files")
    file = models.OneToOneField(File, on_delete=models.CASCADE, default=1)
    trashed_at = models.DateTimeField(verbose_name="Date Trashed", auto_now_add=True)

    def __str__(self):
          return f'{self.user.username}-{self.file.file_name}-Trash'

    # this function is built the remaining days for a file to be deleted
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



class Link(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name="link")
    link = models.CharField(max_length=255)


    def __str__(self):
        return f'{self.user.username}-{self.file.file_name}'


@receiver(post_save, sender=File)
def create_dynamic_link(sender, instance=None, created=False, **kwargs):
    if created:
        link = rand_link(100)
        Link.objects.create(user=instance.uploader, file=instance, link=link)
