from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, BaseUserManager, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from storage_package.models import StoragePackage
from django.db.models import F
# profile image resizing imports
import uuid
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models
import os
from django.db import transaction

# this class is for resizing images
class ResizeImageMixin:
    def resize(self, imageField: models.ImageField, size:tuple):
        im = Image.open(imageField)  # Catch original
        source_image = im.convert('RGB')

        source_image.thumbnail(size)  # Resize to size
        output = BytesIO()
        source_image.save(output, format='JPEG', quality=100) # Save resize image to bytes
        output.seek(0)

        content_file = ContentFile(output.read())  # Read output and create ContentFile in memory
        file = File(content_file)

        random_name = f'{uuid.uuid4()}.jpeg'
        imageField.save(random_name, file, save=False)


# this function is for initializing profile image file path
def get_profile_image_path(self, filename):
    return f'{settings.PROFILE_IMAGES_URL}/{self.username}/{filename}'

# Not used
# this function is for getting the default profile image path
def get_default_profile_image():
    return f'{settings.PROFILE_IMAGES_URL}/avatar.png'

# this class is for overriding default users manager of django user model
class MyAccountManager(BaseUserManager):

    def create_user(self, email, username, password=None, is_staff=False, is_superuser=False):
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise VlaueError('User must have a username')

        user = self.model(
                        email=self.normalize_email(email),
                        username=username,
                        is_staff=is_staff,
                        is_superuser=is_superuser
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    @transaction.atomic
    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
            is_staff = True,
            is_superuser = True
        )
        user.save(using = self._db)
        return user

# Account Model
class Account(AbstractBaseUser, PermissionsMixin, ResizeImageMixin):
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True, validators=[UnicodeUsernameValidator()])
    job_title = models.CharField(max_length=30)
    date_joined = models.DateTimeField(verbose_name="Date Joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="Last Login", auto_now=True)
    image = models.ImageField(upload_to=get_profile_image_path, blank=True, null=True)
    is_active = models.BooleanField('Active status', default=True)
    is_staff = models.BooleanField('Staff status', default=False)

    objects = MyAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return self.email

    # resize profile image before saving
    def save(self, created=None, *args, **kwargs):
        if self.pk:
            if self.image:
                self.resize(self.image, (315, 315))

        super().save(*args, **kwargs)

    def used_storage(self):
        storage = 0
        files = self.files.all()
        for file in files:
            storage += file.file_size

        return storage

    def get_classified_files(self):
        return classify_files(self.files.all())

# this is a receiver for creating an auth token for the user after creating his profile
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# this receiver is for creating and initializing user drive settings after creating his profile
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_drive_settings(sender, instance=None, created=False, **kwargs):
    if created:
        if instance.is_superuser:
            DriveSettings.objects.create(user=instance, unlimited_storage=True)
        else:
            DriveSettings.objects.create(user=instance)



# Not Used
# This receiver renames user drive directory on username change
# @receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_username_dir(sender, instance=None, created=False, **kwargs):
    if created:
        # Create new user dir
        user_path = os.path.join(
            settings.MEDIA_ROOT,
            settings.DRIVE_PATH,
            str(instance.unique_id)
        )
        # Create user Dir
        os.mkdir(user_path)

#Not Used
# This receiver renames user drive directory on username change
#@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def rename_username_dir(sender, instance=None, created=False, **kwargs):
    if instance.id is not None:
        previous = Account.objects.get(id=instance.id)
        if previous.username != instance.username:  # username will be updated
            user_dir_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                previous.username
            )

            # Check if this dir already exists
            if os.path.exists(user_dir_path):
                # Set new user dir
                new_user_dir_path = os.path.join(
                    settings.MEDIA_ROOT,
                    settings.DRIVE_PATH,
                    instance.username
                )
                # Rename user Dir
                os.rename(user_dir_path, new_user_dir_path)

# Not used
# this receiver is to toggle unlimited storage based on user's role
# @receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def on_any_change(sender, instance=None, created=False, **kwargs):
    if instance.id is not None:
        if instance.is_superuser:
            instance.drive_settings.unlimited_storage = True
            instance.drive_settings.save()

# Tis class is for Drive Settings Model for the user
class DriveSettings(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="drive_settings")
    storage_package = models.ForeignKey(StoragePackage, default=StoragePackage.get_default_package, on_delete=models.CASCADE, related_name="package")
    storage_uploaded = models.FloatField(help_text="Storage in GB.", default=0)
    unlimited_storage = models.BooleanField(default=False)


    class Meta:
        verbose_name_plural = "Drive Settings"

    def __str__(self):
        return self.user.username

    def get_used_storage_percentage(self):
        """
        This function returns percentage used of user's storage
        """
        if self.unlimited_storage:
            return 0
        return (self.storage_uploaded/self.storage_package.storage)*100

    def get_storage_limit_in_bytes(self):
        """
        This function returns user's storage in bytes
        """
        if self.unlimited_storage:
            return 0
        return self.storage_package.storage * 1073741824

    def get_storage_uploaded_in_bytes(self):
        """
        This function returns user's used storage in bytes
        """
        return self.storage_uploaded * 1073741824

    def add_storage_uploaded(self, file_size):
        """
        This function add the uploaded file size to the uploaded storage of the user
        """
        self.storage_uploaded =  F('storage_uploaded') + file_size / 1073741824

    def subtract_storage_uploaded(self, file_size):
        """
        This function subtract the deleted file size from the uploaded storage of the user
        """
        self.storage_uploaded =  F('storage_uploaded') -  file_size / 1073741824


    def is_allowed_to_upload_files(self, files_size):
        """
        This function returns True if the user not reached his upload limit, otherwise returns False
        """
        if self.unlimited_storage:
            return True

        elif self.storage_uploaded < self.storage_package.storage:
            storage_after_upload = self.storage_uploaded + (files_size / 1073741824)
            if storage_after_upload < self.storage_package.storage:
                return True

        return False


class Activity(models.Model):
    UPLOAD_FILE = 'UPLOADFILE'
    TRASH_FILE = 'TRASHFILE'
    DELETE_FILE = 'DELETEFILE'
    CREATE_FOLDER = 'CREATEFOLDER'
    DELETE_FOLDER = 'DELETEFOLDER'
    RECOVER_FILE = 'RECOVERFILE'
    ACTIVITY_TYPES = (
        (UPLOAD_FILE, 'Upload File'),
        (TRASH_FILE, 'Trash File'),
        (DELETE_FILE, 'Delete File'),
        (RECOVER_FILE, 'Recover file'),
        (CREATE_FOLDER, 'Create Folder'),
        (DELETE_FOLDER, 'Delete Folder'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    date = models.DateTimeField(auto_now_add=True)

    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        return f'{self.user.username}-{self.get_activity_type_display()}'




def classify_files(files):
    """
    This function is for classifying files
    """

    docs_ext =  ['pdf','doc','docx','xls','ppt','txt']

    classified_files = {
        'images':{'count': 0, 'size':0},
        'videos':{'count': 0, 'size':0},
        'audio':{'count': 0, 'size':0},
        'docs':{'count': 0, 'size':0},
        'others':{'count': 0, 'size':0}
    }

    for file in files:
        if file.file_type.split('/')[0] == 'image':
            classified_files['images']['count'] += 1
            classified_files['images']['size'] += file.file_size

        elif file.file_type.split('/')[0] == 'audio':
            classified_files['audio']['count'] += 1
            classified_files['audio']['size'] += file.file_size


        elif file.file_type.split('/')[0] == 'video':
            classified_files['videos']['count'] += 1
            classified_files['videos']['size'] += file.file_size


        elif file.file_name.split('.')[-1] in docs_ext or file.file_type.split('/')[0] == 'text':
            classified_files['docs']['count'] += 1
            classified_files['docs']['size'] += file.file_size


        else:
            classified_files['others']['count'] += 1
            classified_files['others']['size'] += file.file_size
    return classified_files
