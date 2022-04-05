from django.urls import path
from drive.views import filter, privacy_settings, download_compressed_data, compress_user_files

app_name = 'drive'

urlpatterns = [
    path('category/<str:cat>', filter, name='category'),
    path('privacy/', privacy_settings, name='privacy'),
    path('download/', download_compressed_data, name='download_compressed_data'),
    path('compress-data/', compress_user_files, name='compress_user_files'),

]
