from django.db import models
from django.conf import settings
from datetime import datetime
from django.contrib.sites.models import Site
from datetime import datetime, timezone
import os
import shutil
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_clamd.validators import validate_file_infection
from django.contrib.contenttypes.fields import GenericRelation
from activity.models import Activity
from uploader.utils import generate_file_link

# image compression imports
import sys
from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import uuid

User = settings.AUTH_USER_MODEL

# this function is for initializing file path
def get_file_path(self, filename):

    # # Get current date
    # date = datetime.now()
    # year = str(date.strftime('%Y'))
    # month = str(date.strftime('%m'))
    # day = str(date.strftime('%d'))

    # # Add random string to filename
    # name = filename.rsplit('.', 1)[0]
    # ext = filename.rsplit('.', 1)[1]
    # random_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    # filename = name + '_' + random_text + '.' + ext

    # Get folder tree to save
    if self.parent_folder:
        folder_tree = self.parent_folder.get_folder_tree_as_dirs()
        return f'{settings.DRIVE_PATH}/{str(self.uploader.unique_id)}/{folder_tree}/{filename}'

    return f'{settings.DRIVE_PATH}/{str(self.uploader.unique_id)}/{filename}'





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


# Folder Model
class Folder(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "folders")
    name = models.CharField(default="New Folder", max_length=30)
    parent_folder = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name="Date Created", auto_now_add=True)
    activities = GenericRelation(Activity)


    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.username}-{self.name}'

    def get_absolute_url(self):
        return f'/uploader/folder/{self.unique_id}'

    def get_files_count(self):
        return self.files.filter(trash=None).count()

    # This function id to return folder tree as objects [<folder_obj2>, <folder_obj2>, <folder_obj3>]
    # Not Used
    def recursive(self):
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

    # This function id to return folder tree as objects [<folder_obj2>, <folder_obj2>, <folder_obj3>]
    # Recursion
    def get_folder_tree(self, folder=None, folder_tree=None):

        if folder_tree is None:
            folder_tree = []
            folder = self

        if not folder.parent_folder:
            folder_tree.append(folder)
            folder_tree.reverse()
            return folder_tree
        else:
            folder_tree.append(folder)
            return self.get_folder_tree(folder.parent_folder, folder_tree)



    # This function is to return folder tree in a format like folder1/folder2/folder3
    def get_folder_tree_as_dirs(self):
        folder_tree = self.get_folder_tree()
        folder_tree = [folder.name for folder in folder_tree]
        folder_tree_dirs = '/'.join(folder_tree)
        return folder_tree_dirs

# This receiver is to create folder dir in physical storage
@receiver(post_save, sender=Folder)
def create_folder_dir(sender, instance=None, created=False, **kwargs):

    if created:
        if instance.parent_folder:
            folder_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(instance.user.unique_id),
                instance.parent_folder.get_folder_tree_as_dirs(),
                instance.name)
        else:
            folder_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(instance.user.unique_id),
                instance.name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)

# This receiver is to record user activity
@receiver(post_save, sender=Folder)
def record_activity_on_creating_folder(sender, instance=None, created=False, **kwargs):
    if created:
        instance.activities.create(
            activity_type=Activity.CREATE_FOLDER,
            user=instance.user,
            object_name=instance.name
        )

# This function is for recording activity of folder
@receiver(post_delete, sender=Folder)
def record_activity_on_deleting_folder(sender, instance, **kwargs):
    instance.activities.create(
        activity_type=Activity.DELETE_FOLDER,
        user=instance.user,
        object_name=instance.name
    )


# File Model
class File(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "files")
    file = models.FileField(upload_to=get_file_path)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    file_type = models.CharField(max_length=255)
    file_category = models.CharField(max_length=30)
    uploaded_at = models.DateTimeField(verbose_name="Date Uploaded", auto_now_add=True)
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files", null=True, blank=True)
    activities = GenericRelation(Activity)


    class Meta:
        ordering = ('-uploaded_at',)

    def __str__(self):
        return self.file.name

    def get_url(self):
        return 'http://%s/%s/%s' % (Site.objects.get_current().domain, settings.ALIAS_DRIVE_PATH, self.privacy.link)

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

# This function is for recording activity of a file
@receiver(post_save, sender=File)
def record_activity_on_upload_file(sender, instance=None, created=False, **kwargs):
    if created:
        instance.activities.create(
            activity_type=Activity.UPLOAD_FILE,
            user=instance.uploader,
            object_name=instance.file_name
        )

# This function is for recording activity of a file
@receiver(post_delete, sender=File)
def record_activity_on_delete_file(sender, instance, **kwargs):
    instance.activities.create(
        activity_type=Activity.DELETE_FILE,
        user=instance.uploader,
        object_name=instance.file_name
    )

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
    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='privacy')
    option = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default="private")
    shared_with = models.ManyToManyField(User, blank=True)
    link = models.CharField(max_length=255, unique=True, null=True)

    def __str__(self):
        return f'{self.file.uploader.username}-{self.file.parent_folder}-{self.file.file_name}'

    def save(self, *args, **kwargs):
        self.link = generate_file_link(self.file.file_name)
        super().save(*args, **kwargs)



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
