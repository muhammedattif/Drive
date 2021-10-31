from django.urls import path
from drive.views import filter

app_name = 'drive'

urlpatterns = [
    path('category/<str:cat>', filter, name='category'),
]
