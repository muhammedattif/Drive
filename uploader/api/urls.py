from django.urls import path
from uploader.api.views import upload, delete
app_name = 'uploader'

urlpatterns = [
    path('upload', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),

  ]
