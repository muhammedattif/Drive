from django.urls import path
from uploader.views import upload, delete, filter

app_name = 'uploader'

urlpatterns = [
    path('', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),
    path('category/<str:cat>', filter, name='category')
  ]
