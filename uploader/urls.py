from django.urls import path
from uploader.views import upload, download, move_to_trash, filter, get_trashed_files, recover, delete_file, folder, file_settings, create_folder, delete_folder

app_name = 'uploader'

urlpatterns = [
    path('', upload, name='upload'),
    # path('<str:unique_id>/download', download, name='download'),
    path('<str:unique_id>/move_to_trash', move_to_trash, name='move_to_trash'),
    path('<str:unique_id>/delete_file', delete_file, name='delete_file'),
    path('category/<str:cat>', filter, name='category'),
    path('trash', get_trashed_files, name='trash'),
    path('<str:unique_id>/recover', recover, name='recover'),
    path('create_folder/<str:unique_id>', create_folder, name='create_folder'),
    path('delete_folder/<str:unique_id>', delete_folder, name='delete_folder'),
    path('folder/<str:unique_id>', folder, name='folder'),
    path('file_settings/<str:unique_id>', file_settings, name='file_settings'),

  ]
