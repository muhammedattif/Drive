from django.urls import path
from folder.api.views import create_folder_tree, delete_folder

app_name = 'uploader'

urlpatterns = [
    path('create_folder', create_folder_tree, name='create_folder'),
    path('delete_folder', delete_folder, name='delete_folder')
]
