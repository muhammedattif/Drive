from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.' + env('DATABASE_ENGINE'),
        'NAME': BASE_DIR / env('DATABASE_NAME'),
    }
}
