from django.urls import path
from file.views import (
upload,
download,
move_to_trash,
get_trashed_files,
recover,
delete_file,
file_settings,
convert_file_quality,
stream,
shared_with
)

app_name = 'file'

urlpatterns = [
    path('', upload, name='upload'),
    path('<str:unique_id>/shared_with', shared_with, name='shared_with'),
    path('<str:unique_id>/move_to_trash', move_to_trash, name='move_to_trash'),
    path('<str:unique_id>/delete_file', delete_file, name='delete_file'),
    path('<str:unique_id>/delete_file/<str:quality>', delete_file, name='delete_converted_file'),
    path('<str:unique_id>/convert/<str:quality>', convert_file_quality, name='convert_file_quality'),
    path('trash', get_trashed_files, name='trash'),
    path('<str:unique_id>/recover', recover, name='recover'),
    path('<str:unique_id>/file_settings', file_settings, name='file_settings'),
    path('stream/', stream)
]
