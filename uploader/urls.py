from django.urls import path
from uploader.views import upload, move_to_trash, filter, get_trashed_files, recover, delete

app_name = 'uploader'

urlpatterns = [
    path('', upload, name='upload'),
    path('<int:id>/trash', move_to_trash, name='move_to_trash'),
    path('<int:id>/delete', delete, name='delete'),
    path('category/<str:cat>', filter, name='category'),
    path('trash', get_trashed_files, name='trash'),
    path('<int:id>/recover', recover, name='recover')
  ]
