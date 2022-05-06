# Django
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

# Files App
from file.models import FileSharingBlockList

User = get_user_model()

class Command(BaseCommand):
    help = 'Create Block lists for old users'

    def handle(self, *args, **kwargs):

        users = User.objects.filter(file_sharing_block_list=None)
        users_blocklist_objs = []
        for user in users:
            users_blocklist_objs.append(FileSharingBlockList(user=user))

        FileSharingBlockList.objects.bulk_create(users_blocklist_objs)
        self.stdout.write(self.style.SUCCESS(f'{len(users)} rows affected'))
