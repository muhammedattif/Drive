# Standard library
import os
import uuid
from io import BytesIO

# Django
from django.conf import settings
from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files import File
from django.core.files.base import ContentFile
from django.db import models, transaction

# Third-party
from PIL import Image


# this class is for resizing images
class ResizeImageMixin:
    def resize(self, image_field: models.ImageField, size:tuple):
        im = Image.open(image_field)  # Catch original
        source_image = im.convert('RGB')

        source_image.thumbnail(size)  # Resize to size
        output = BytesIO()
        source_image.save(output, format='JPEG', quality=100) # Save resize image to bytes
        output.seek(0)

        content_file = ContentFile(output.read())  # Read output and create ContentFile in memory
        file = File(content_file)

        random_name = f'{uuid.uuid4()}.jpeg'
        image_field.save(random_name, file, save=False)


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

class ActionsType(models.TextChoices):
    ALLOW_ALL = ("allow_all", "Allow all")
    RESTRICTED = ("restricted", "Restricted")

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
    actions_type = models.CharField(
        max_length=15,
        choices=ActionsType.choices,
        default=ActionsType.RESTRICTED,
        help_text="This option limits the user actions of the views."
    )

    objects = MyAccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    def __str__(self):
        return self.email

    # resize profile image before saving
    def save(self, created=None, *args, **kwargs):
        if self.pk and self.image:
            self.resize(self.image, (315, 315))
        super().save(*args, **kwargs)

    def used_storage(self):
        storage = 0
        files = self.files.all()
        for file in files:
            storage += file.size

        return storage

    def get_classified_files(self):
        return classify_files(self.files.all())

    def can_share_with(self, user):
        return (user not in self.file_sharing_block_list.users.all()) and (self not in user.file_sharing_block_list.users.all())




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
    if instance.id is not None and instance.is_superuser:
        instance.drive_settings.unlimited_storage = True
        instance.drive_settings.save()


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
        if file.type.split('/')[0] == 'image':
            classified_files['images']['count'] += 1
            classified_files['images']['size'] += file.size

        elif file.type.split('/')[0] == 'audio':
            classified_files['audio']['count'] += 1
            classified_files['audio']['size'] += file.size


        elif file.type.split('/')[0] == 'video':
            classified_files['videos']['count'] += 1
            classified_files['videos']['size'] += file.size


        elif file.name.split('.')[-1] in docs_ext or file.type.split('/')[0] == 'text':
            classified_files['docs']['count'] += 1
            classified_files['docs']['size'] += file.size


        else:
            classified_files['others']['count'] += 1
            classified_files['others']['size'] += file.size
    return classified_files
