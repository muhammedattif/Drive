from django.urls import path
from file.api.views import (
upload,
delete,
FileDownloadView,
FileCopyView,
FileMoveView,
stream_video,
generate_video_links,
get_conversion_status,
SharedWithListView,
generate_video_links_for_iphone
)

app_name = 'file'

urlpatterns = [
    path('upload', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),
    path('<str:uuid>/download', FileDownloadView.as_view(), name='download'),
    path('<str:uuid>/generate-video-link', generate_video_links),
    path('<str:uuid>/generate-video-link/iphone', generate_video_links_for_iphone),
    path('<str:uuid>/<str:quality>/<str:expiry>/<str:token>/stream', stream_video, name='stream'),
    path('<str:uuid>/conversion_status', get_conversion_status, name='conversion-status'),

    path('<str:uuid>/copy', FileCopyView.as_view(), name='copy'),
    path('<str:uuid>/move', FileMoveView.as_view(), name='move'),
    # Files Sharing URLs
    path('<str:uuid>/shared-with', SharedWithListView.as_view(), name='shared-with'),


]
