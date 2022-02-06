from django.urls import path
from file.views import upload, download, move_to_trash, get_trashed_files, recover, delete_file, file_settings, stream

app_name = 'file'

urlpatterns = [
    path('', upload, name='upload'),
    path('<str:unique_id>/move_to_trash', move_to_trash, name='move_to_trash'),
    path('<str:unique_id>/delete_file', delete_file, name='delete_file'),
    path('trash', get_trashed_files, name='trash'),
    path('<str:unique_id>/recover', recover, name='recover'),
    path('file_settings/<str:unique_id>', file_settings, name='file_settings'),
    path('stream/', stream)
]
