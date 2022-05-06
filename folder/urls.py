# django
from django.urls import path

# Local Django
from folder.views import (create_folder, delete_folder, download_folder,
                          folder, rename_folder, shared_with)

app_name = 'folder'

urlpatterns = [
    path('<str:unique_id>', folder, name='folder'),
    path('<str:unique_id>/shared_with', shared_with, name='shared_with'),
    path('<str:unique_id>/create', create_folder, name='create_folder'),
    path('<str:unique_id>/delete', delete_folder, name='delete_folder'),
    path('<str:unique_id>/rename', rename_folder, name='rename_folder'),
    path('<str:unique_id>/download', download_folder, name='download')
]
