from django.urls import path
from folder.views import folder, create_folder, delete_folder, rename_folder

app_name = 'folder'

urlpatterns = [
    path('<str:unique_id>', folder, name='folder'),
    path('<str:unique_id>/create', create_folder, name='create_folder'),
    path('<str:unique_id>/delete', delete_folder, name='delete_folder'),
    path('<str:unique_id>/rename', rename_folder, name='rename_folder')
]
