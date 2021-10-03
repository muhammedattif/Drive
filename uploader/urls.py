from django.urls import path
from uploader.views import upload, move_to_trash, filter, get_trashed_files, recover, delete_file, folder, file_settings, create_folder, delete_folder

app_name = 'uploader'

urlpatterns = [
    path('', upload, name='upload'),
    path('<int:id>/move_to_trash', move_to_trash, name='move_to_trash'),
    path('<int:id>/delete_file', delete_file, name='delete_file'),
    path('category/<str:cat>', filter, name='category'),
    path('trash', get_trashed_files, name='trash'),
    path('<int:id>/recover', recover, name='recover'),
    path('create_folder/<int:id>', create_folder, name='create_folder'),
    path('delete_folder/<int:id>', delete_folder, name='delete_folder'),
    path('folder', folder, name='folder'),
    path('folder/<int:id>', folder, name='folder'),
    path('file_settings/<int:id>', file_settings, name='file_settings'),

  ]
