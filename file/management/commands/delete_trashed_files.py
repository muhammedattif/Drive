from django.core.management.base import BaseCommand
from file.cron import delete_trashed_files
from django.conf import settings

class Command(BaseCommand):
    help = f'Delete trashed files after {settings.TRASH_DAYS} day'

    def handle(self, *args, **kwargs):
        delete_trashed_files()
        self.stdout.write(self.style.ERROR('Files deleted'))
