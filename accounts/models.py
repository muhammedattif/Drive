from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.db.models import F
# profile image resizing imports
import uuid
from PIL import Image
from io import BytesIO
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models


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

    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('User must have an email address')
        if not username:
            raise VlaueError('User must have a username')

        user = self.model(
                        email=self.normalize_email(email),
                        username=username
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(email=self.normalize_email(email),password=password,username=username)

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

# Account Model
class Account(AbstractBaseUser, ResizeImageMixin):

    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    job_title = models.CharField(max_length=30)
    date_joined = models.DateTimeField(verbose_name="Date Joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="Last Login", auto_now=True)
    image = models.ImageField(upload_to=get_profile_image_path, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = MyAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']



    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def used_storage(self):
        storage = 0
        files = self.files.all()
        for file in files:
            storage += file.file_size

        return storage

    def get_classified_files(self):
        return classify_files(self.files.all())

    # resize profile image before saving
    def save(self, created=None, *args, **kwargs):
        if self.pk:
            if self.image:
                self.resize(self.image, (315, 315))

        super().save(*args, **kwargs)

# this is a receiver for creating an auth token for the user after creating his profile
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

# this receiver is for creating and initializing user drive settings after creating his profile
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_drive_settings(sender, instance=None, created=False, **kwargs):
    if created:
        DriveSettings.objects.create(user=instance)

# Tis class is for Drive Settings Model for the user
class DriveSettings(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name="drive_settings")
    storage_limit = models.FloatField(help_text="Storage in GB.", default=settings.MAX_STORAGE_LIMIT)
    storage_uploaded = models.FloatField(help_text="Storage in GB.", default=0)

    class Meta:
        verbose_name_plural = "DriveSettings"

    def __str__(self):
        return self.user.username

    def get_used_storage_percentage(self):
        """
        This function returns percentage used of user's storage
        """
        return (self.storage_uploaded/self.storage_limit)*100

    def get_storage_limit_in_bytes(self):
        """
        This function returns user's storage in bytes
        """
        return self.storage_limit * 1073741824

    def get_storage_uploaded_in_bytes(self):
        """
        This function returns user's used storage in bytes
        """
        return self.storage_uploaded * 1073741824

    def add_storage_uploaded(self, file_size):
        """
        This function add the uploaded file size to the uploaded storage of the user
        """
        self.storage_uploaded =  self.storage_uploaded + file_size / 1073741824

    def subtract_storage_uploaded(self, file_size):
        """
        This function subtract the deleted file size from the uploaded storage of the user
        """
        self.storage_uploaded =  self.storage_uploaded -  file_size / 1073741824


    def is_allowed_to_upload_files(self, files_size):
        """
        This function returns True if the user not reached his upload limit, otherwise returns False
        """
        if self.storage_uploaded < self.storage_limit:
            storage_after_upload = self.storage_uploaded + (files_size / 1073741824)
            if storage_after_upload < self.storage_limit:
                return True

        return False



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
