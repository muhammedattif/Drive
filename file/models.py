from django.db import models
from django.conf import settings
from folder.models import Folder
from activity.models import Activity
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from file.utils import generate_file_link, get_file_path, get_video_cover_path, get_video_subtitle_path, compress_image
import uuid
from datetime import datetime, timezone
from model_utils import Choices
from .validators import validation_message
from django.template.defaultfilters import truncatechars

User = get_user_model()

QUALITY_CHOICES = (
        ('144p', '144p'),
        ('240p', '240p'),
        ('360p', '360p'),
        ('480p', '480p'),
        ('720p', '720p'),
        ('1080p', '1080p'),
    )


class SharedObject(models.Model):
    shared_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_files")

    object_choices = models.Q(app_label = 'file', model = 'file') | models.Q(app_label = 'folder', model = 'folder')

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=object_choices, related_name='shared_with')
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shared_with_me")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at',]
        unique_together = ['shared_by', 'content_type', 'object_id', 'shared_with']

    def clean(self):
        if self.shared_by != self.content_object.user:
            raise validation_message('not_file_owner')

        if not self.shared_by.can_share_with(self.shared_with):
            raise validation_message('in_block_list')

        super(SharedObject, self).clean()

    def __str__(self):
        return f'{self.shared_by.username}-{self.content_object.name}-{self.shared_with.username}'

class SharedObjectPermission(models.Model):
    file = models.OneToOneField(SharedObject, on_delete=models.CASCADE, related_name='permissions')
    can_view = models.BooleanField(default=True)
    can_rename = models.BooleanField(default=False)
    can_download = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.file.id}'

    def clean(self):

        if self.can_rename and not self.file.content_object.user.has_perm('folder.can_rename_folder'):
            raise validation_message('rename_folder_permission_denied')

        if self.can_download and not self.file.content_object.user.has_perm('folder.can_download_folder'):
            raise validation_message('download_folder_permission_denied')

        super(SharedObjectPermission, self).clean()

class FileSharingBlockList(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='file_sharing_block_list')
    users = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.user.email


# File Model
class File(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=get_file_path, max_length=500)
    name = models.CharField(max_length=255)
    size = models.IntegerField()
    type = models.CharField(max_length=255)
    category = models.CharField(max_length=30)
    uploaded_at = models.DateTimeField(verbose_name="Date Uploaded", auto_now_add=True)
    parent_folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name="files", null=True, blank=True)
    activities = GenericRelation(Activity)
    shared_with = GenericRelation(SharedObject)

    class Meta:
        ordering = ('-uploaded_at',)
        permissions = (
            ("can_download_file", "Can Download File"),
            ("can_stream_media_files", "Can Stream Media Files"),
        )

    def __str__(self):
        return self.name[:20]

    def get_url(self):
        return 'https://%s/%s/%s' % (Site.objects.get_current().domain, settings.ALIAS_DRIVE_PATH, self.privacy.link)

    def is_private(self):
        return self.privacy.option == 'private'

    def is_public(self):
        return self.privacy.option == 'public'

    @property
    def file_name(self):
        return truncatechars(self.name, 20)

    def is_shared_with(self, user):

        shared_object = SharedObject.objects.filter(
        shared_with=user,
        object_id=self.id,
        content_type=ContentType.objects.get(model='file')
        ).first()

        if shared_object:
            return shared_object, True
        else:
            file_tree = self.parent_folder.get_folder_tree()
            all_folders_shared_with_user = SharedObject.objects.prefetch_related('content_object__parent_folder').filter(shared_with=user, content_type=ContentType.objects.get(model='folder'))
            for object in all_folders_shared_with_user:
                if self.parent_folder == object.content_object or object.content_object in file_tree:
                    return object, True
            return None, False

    # this save method is used to hardcode file field
    # if the uploaded file is an image then it will be compressed
    # def save(self, *args, **kwargs):
    #     if not self.id and (self.type.split('/')[1].lower() == 'jpeg' or self.type.split('/')[1].lower() == 'jpg' or
    #         self.type.split('/')[1].lower() == 'png') and not self.id:
    #         self.file = compress_image(self.file, self.type)
    #         self.size = self.file.size
    #     super().save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if self.id:
            # Change File path in case it moved to anothe path
            old_file = File.objects.get(id=self.id)
            if old_file.parent_folder != self.parent_folder:
                if self.parent_folder:
                    parent_folder_path = self.parent_folder.get_folder_tree_as_dirs()
                    base_dir = f'{settings.DRIVE_PATH}/{str(self.user.unique_id)}'
                    new_path = f'{base_dir}/{parent_folder_path}/{self.name}'
                else:
                    base_dir = f'{settings.DRIVE_PATH}/{str(self.user.unique_id)}'
                    new_path = f'{base_dir}/{self.name}'

                if str(self.file) != new_path:
                    self.file.name = new_path
        super().save(*args, **kwargs)

class FileQuality(models.Model):

    STATUS_CHOICES = (
        ('converting', 'Converting'),
        ('converted', 'Converted'),
        ('failed', 'Failed'),
    )

    original_file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='qualities')
    quality = models.CharField(max_length=100, choices=QUALITY_CHOICES, default='144p')
    converted_file = models.ForeignKey(File, on_delete=models.CASCADE, null=True)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='converting')

    class Meta:
        verbose_name_plural = 'File Qualities'
        unique_together = ['original_file', 'quality']
        permissions = (
            ("can_convert_media_files", "Can Convert Media Files"),
        )

    def __str__(self):
        return f'{self.original_file.name}->{self.quality}'


class MediaFileProperties(models.Model):

    media_file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='properties')
    cover = models.FileField(upload_to=get_video_cover_path, max_length=500, blank=True)
    quality = models.CharField(max_length=100, choices=QUALITY_CHOICES, default='144p')
    converted = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.media_file.name}->{self.converted}'

class VideoSubtitle(models.Model):

    LANGUAGE_CHOICES = (
        ('en', 'English'),
        ('ar', 'Arabic')
    )

    media_file = models.ForeignKey(MediaFileProperties, on_delete=models.CASCADE, related_name='subtitles')
    language = models.CharField(max_length=100, choices=LANGUAGE_CHOICES, default='en')
    subtitle_file = models.FileField(upload_to=get_video_subtitle_path, max_length=500)

    def __str__(self):
        return f'{self.media_file.media_file.name}->{self.language}'


class FilePrivacy(models.Model):
    PRIVACY_CHOICES = (
        ('public', 'Public'),
        ('friends', 'Friends'),
        ('private', 'Private'),
    )
    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='privacy')
    option = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default="private")
    accessed_by = models.ManyToManyField(User, blank=True, help_text="List of users that can access this file with the sharable link.")
    link = models.CharField(max_length=255, unique=True, null=True)


    def save(self, *args, **kwargs):
        if not self.link:
            self.link = generate_file_link(self.file.name)

        if not self.pk:
            self.option = self.file.user.drive_settings.default_upload_privacy

        super().save(*args, **kwargs)


class Trash(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="trashed_files")
    file = models.OneToOneField(File, on_delete=models.CASCADE, default=1)
    trashed_at = models.DateTimeField(verbose_name="Date Trashed", auto_now_add=True)

    class Meta:
        permissions = (
            ("can_add_files_to_trash", "Can add Files to Trash"),
            )

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
