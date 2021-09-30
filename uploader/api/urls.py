from django.urls import path
from uploader.api.views import upload, delete, create_folder, delete_folder
app_name = 'uploader'

urlpatterns = [
    path('upload', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),
    path('create_folder', create_folder, name='create_folder'),
    path('delete_folder', delete_folder, name='delete_folder'),

  ]
