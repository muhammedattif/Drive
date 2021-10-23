from django.core.management.base import BaseCommand
from uploader.cron import delete_trashed_files

class Command(BaseCommand):
    help = f'Delete trashed files after {settings.TRASH_DAYS} day'

    def handle(self, *args, **kwargs):
        delete_trashed_files()
        self.stdout.write(self.style.ERROR('Files deleted'))
