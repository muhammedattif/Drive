from django.urls import path
from file.api.views import upload, delete
app_name = 'file'

urlpatterns = [
    path('upload', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),

  ]
