from __future__ import absolute_import, unicode_literals

import os
from os.path import dirname, join

import dotenv
from celery import Celery
from django.conf import settings

project_dir = dirname(dirname(__file__))
dotenv.read_dotenv(join(project_dir, '.env'))

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloud.settings.' + os.environ.get('ENVIRONMENT'))

app = Celery('cloud')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
