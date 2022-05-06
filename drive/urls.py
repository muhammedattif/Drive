# Django
from django.urls import path

# Drive App
from drive.views import (compress_user_files, download_compressed_data,
                         erase_account_data, filter, privacy_settings,
                         shared_with_me, shared_with_me_detail)

app_name = 'drive'

urlpatterns = [
    path('category/<str:cat>', filter, name='category'),
    path('privacy/', privacy_settings, name='privacy'),
    path('download/', download_compressed_data, name='download_compressed_data'),
    path('compress-data/', compress_user_files, name='compress_user_files'),
    path('erase/', erase_account_data, name='erase_account_data'),
    path('shared-with-me/<int:sharing_id>', shared_with_me_detail, name='shared-with-me-detail'),
    path('shared-with-me', shared_with_me, name='shared-with-me')

]
