"""
Django settings for cloud project.

Generated by 'django-admin startproject' using Django 3.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import environ
from pathlib import Path
import os

env = environ.Env()
# reading .env file
environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

AUTH_USER_MODEL = "accounts.Account"

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.AllowAllUsersModelBackend',
    'accounts.backends.CaseInsensitiveModelBackend'
)
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Allowed hosts
ALLOWED_HOSTS = [env('ALLOWED_HOST')]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.redirects',
    'django.contrib.sites',
    'rest_framework',
    'rest_framework.authtoken',
    'django.contrib.humanize',
    'mathfilters',
    'bootstrap4',
    # for scanning from virus
    'django_clamd',
    # this is for CRONJOBS
    'django_crontab',
    # CORS
    'corsheaders',

    # APPS
    'accounts',
    'drive',
    'folder',
    'file',
    'activity',
    'storage_package'
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    #CORS
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = [
'DELETE',
'GET',
'OPTIONS',
'PATCH',
'POST',
'PUT',
]

CORS_ALLOW_HEADERS = [
'accept',
'accept-encoding',
'authorization',
'content-type',
'dnt',
'origin',
'user-agent',
'x-csrftoken',
'x-requested-with',
]

ROOT_URLCONF = 'cloud.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cloud.wsgi.application'



REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Cairo'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# schedule tasks
CRONJOBS = [
    ('* * * * *', 'uploader.cron.delete_trashed_files')
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / "general_static",
]

STATIC_ROOT = os.path.join(BASE_DIR, "static")

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = '/media/'
# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Days to delete files in Trash
TRASH_DAYS = 30

SUB_FOLDERS_LIMIT = 10

# Directory where users uploads are gonna be stored
PROFILE_IMAGES_URL = 'profile_images'

# Directory where other uploaded files are gonna be stored
DRIVE_PATH = 'drive'
os.makedirs(os.path.join(MEDIA_ROOT, DRIVE_PATH), exist_ok=True)
# Alias for drive path
ALIAS_DRIVE_PATH = 'link'

# Basic Storage Package Variables
# Once this values have changed, you have to run the following command to apply the new changes:
# --> python manage.py migrate_to_new_default_storage_package
BASIC_PACKAGE_NAME = 'Basic'
BASIC_PACKAGE_STORAGE_LIMIT = 15 # number in GB
