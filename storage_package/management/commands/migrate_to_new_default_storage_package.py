# Django
from django.conf import settings
from django.core.management.base import BaseCommand

# local Django
from storage_package.models import StoragePackage


class Command(BaseCommand):
    help = f'Migrate to new default Storage Package.'

    def handle(self, *args, **kwargs):
        try:
            old_default_package = StoragePackage.objects.get(default=True)
            old_default_package.name = settings.BASIC_PACKAGE_NAME
            old_default_package.storage = settings.BASIC_PACKAGE_STORAGE_LIMIT
            old_default_package.save()
            self.stdout.write(self.style.SUCCESS('New Package Migrated Successfully'))
        except exception as e:
            self.stdout.write(self.style.ERROR(f'Error {e}'))
