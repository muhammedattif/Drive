from django.core.management.base import BaseCommand
from django.conf import settings
from file.models import FileSharingBlockList
from django.contrib.auth import get_user_model

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
