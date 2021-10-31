from django.urls import path
from folder.views import folder, create_folder, delete_folder

app_name = 'folder'

urlpatterns = [
    path('<str:unique_id>', folder, name='folder'),
    path('create_folder/<str:unique_id>', create_folder, name='create_folder'),
    path('delete_folder/<str:unique_id>', delete_folder, name='delete_folder')
]
