from django.urls import path
from drive.views import filter, privacy_settings

app_name = 'drive'

urlpatterns = [
    path('category/<str:cat>', filter, name='category'),
    path('privacy/', privacy_settings, name='privacy'),

]
