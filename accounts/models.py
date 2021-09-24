from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
# Create your models here.

class MyAccountManager(BaseUserManager):

    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError('User must have an email addredd')
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

class Account(AbstractBaseUser):

    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    job_title = models.CharField(max_length=30)
    date_joined = models.DateTimeField(verbose_name="Date Joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="Last Login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = MyAccountManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def used_storege(self):
        storage = 0
        files = self.files.all()
        for file in files:
            storage += file.file_size

        return storage

    def get_classified_files(self):
        return classify_files(self.files.all())

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

def classify_files(files):

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
            continue

        elif file.file_type.split('/')[0] == 'audio':
            classified_files['audio']['count'] += 1
            classified_files['audio']['size'] += file.file_size
            continue

        elif file.file_type.split('/')[0] == 'video':
            classified_files['videos']['count'] += 1
            classified_files['videos']['size'] += file.file_size
            continue

        elif file.file_name.split('.')[-1] in docs_ext or file.file_type.split('/')[0] == 'text':
            classified_files['docs']['count'] += 1
            classified_files['docs']['size'] += file.file_size
            continue
        else:
            classified_files['others']['count'] += 1
            classified_files['others']['size'] += file.file_size
    return classified_files
