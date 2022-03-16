from django.db import models
from django.conf import settings
from accounts.models import Account
from folder.models import Folder
from activity.models import Activity
from django.contrib.sites.models import Site
from django.contrib.contenttypes.fields import GenericRelation
from file.utils import generate_file_link, get_file_path, get_video_cover_path, get_video_subtitle_path, compress_image
import uuid
from datetime import datetime, timezone
from model_utils import Choices
from django.core.exceptions import ValidationError


# File Model
class File(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    uploader = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=get_file_path, max_length=500)
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
        return self.file_name

    def get_url(self):
        return 'https://%s/%s/%s' % (Site.objects.get_current().domain, settings.ALIAS_DRIVE_PATH, self.privacy.link)

    def is_private(self):
        return self.privacy.option == 'private'

    def is_public(self):
        return self.privacy.option == 'public'

    # this save method is used to hardcode file field
    # if the uploaded file is an image then it will be compressed
    # def save(self, *args, **kwargs):
    #     if not self.id and (self.file_type.split('/')[1].lower() == 'jpeg' or self.file_type.split('/')[1].lower() == 'jpg' or
    #         self.file_type.split('/')[1].lower() == 'png') and not self.id:
    #         self.file = compress_image(self.file, self.file_type)
    #         self.file_size = self.file.size
    #     super().save(*args, **kwargs)

class FileQuality(models.Model):

    QUALITY_CHOICES = (
        ('144p', '144p'),
        ('240p', '240p'),
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    )

    STATUS_CHOICES = (
        ('converting', 'Converting'),
        ('converted', 'Converted'),
        ('failed', 'Failed'),
    )

    original_file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='qualities')
    quality = models.CharField(max_length=100, choices=QUALITY_CHOICES, default='144p')
    converted_file = models.ForeignKey(File, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='processing')

    class Meta:
        verbose_name_plural = 'File Qualities'
        unique_together = ['original_file', 'quality']

    def __str__(self):
        return f'{self.original_file.file_name}->{self.quality}'

    # def clean(self):
    #     if self.original_file == self.converted_file:
    #         raise ValidationError('Original File and the Converted file cannot be the same.')
    #     super(FileQuality, self).clean()


class MediaFileProperties(models.Model):

    QUALITY_CHOICES = (
        ('144p', '144p'),
        ('240p', '1240p'),
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    )

    media_file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='properties')
    cover = models.FileField(upload_to=get_video_cover_path, max_length=500, blank=True)
    quality = models.CharField(max_length=100, choices=QUALITY_CHOICES, default='144p')
    converted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.media_file.file_name}->{self.converted}'

class VideoSubtitle(models.Model):

    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('ar', 'Arabic')
    )

    media_file = models.ForeignKey(MediaFileProperties, on_delete=models.CASCADE, related_name='subtitles')
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES, default='en')
    subtitle_file = models.FileField(upload_to=get_video_subtitle_path, max_length=500)

    def __str__(self):
        return f'{self.media_file.media_file.file_name}->{self.language}'


class FilePrivacy(models.Model):
    PRIVACY_CHOICES = (
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    )
    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='privacy')
    option = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default="private")
    shared_with = models.ManyToManyField(Account, blank=True)
    link = models.CharField(max_length=255, unique=True, null=True)


    def save(self, *args, **kwargs):
        if not self.link:
            self.link = generate_file_link(self.file.file_name)

        if not self.pk:
            self.option = self.file.uploader.drive_settings.default_upload_privacy

        super().save(*args, **kwargs)


class Trash(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="trashed_files")
    file = models.OneToOneField(File, on_delete=models.CASCADE, default=1)
    trashed_at = models.DateTimeField(verbose_name="Date Trashed", auto_now_add=True)

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
