# Third-party
from celery import shared_task


@shared_task
def async_convert_video_quality(original_file_unique_id, quality, user_id):
    from accounts.models import Account
    from file.models import File, FileQuality
    from file.utils import convert_video_quality

    user = Account.objects.get(id=user_id)
    original_file = File.objects.get(unique_id=original_file_unique_id)

    file_quality = FileQuality.objects.create(original_file=original_file, quality=quality)

    converted_video, converted_video_path, converted = convert_video_quality(video_path=original_file.file.path, quality=quality)

    if not converted:
        file_quality.status = 'failed'
        file_quality.save(update_fields=['status'])
        return 'Quality is not supported.'

    file_name = converted_video.name
    file_size = converted_video.size

    converted_video = File.objects.create(user=user, name=file_name, size=file_size,
                                          type=original_file.type,
                                          category=original_file.category, file=str(converted_video_path),
                                          parent_folder=original_file.parent_folder
                                          )
    converted_video.properties.converted = True
    converted_video.properties.save(update_fields=['converted'])

    file_quality.converted_file = converted_video
    file_quality.status = 'converted'
    file_quality.save(update_fields=['status', 'converted_file'])
