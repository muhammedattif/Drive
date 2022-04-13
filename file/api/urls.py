from django.urls import path
from file.api.views import upload, delete, stream_video, generate_video_links, get_conversion_status, SharedFileListCreateView, SharedFileDestroyView
app_name = 'file'

urlpatterns = [
    path('upload', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),
    path('<str:uuid>/generate-video-link', generate_video_links),
    path('<str:uuid>/<str:quality>/<str:expiry>/<str:token>/stream', stream_video, name='stream'),
    path('<str:uuid>/conversion_status', get_conversion_status, name='conversion-status'),

    # Shared Files
    path('<str:uuid>/shared-with', SharedFileListCreateView.as_view(), name='shared-with'),
    path('<str:uuid>/shared-with/<int:id>', SharedFileDestroyView.as_view(), name='delete-shared-with'),

]
