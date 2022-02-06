from django.urls import path
from file.api.views import upload, delete, stream_video, generate_video_link
app_name = 'file'

urlpatterns = [
    path('upload', upload, name='upload'),
    path('<int:id>/delete', delete, name='delete'),
    path('<int:id>/generate-video-link', generate_video_link),
    path('<int:id>/<str:token>/<str:expiry>/stream', stream_video, name='stream')
]
