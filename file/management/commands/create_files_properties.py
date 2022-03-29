from django.core.management.base import BaseCommand
from django.conf import settings
from file.models import File, MediaFileProperties
from file.utils import detect_quality

class Command(BaseCommand):
    help = 'Create Properties for each media file'

    def handle(self, *args, **kwargs):
        files = File.objects.filter(file_category='media', file_type__contains='video', properties=None)
        files_props_objs = []
        for file in files:
            media_file_quality = detect_quality(file.file.path)
            files_props_objs.append(MediaFileProperties(media_file=file, quality=media_file_quality))

        MediaFileProperties.objects.bulk_create(files_props_objs)
        self.stdout.write(self.style.SUCCESS(f'{len(files)} rows affected'))
