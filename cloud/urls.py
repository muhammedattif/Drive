"""cloud URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from django.conf.urls.static import static
from django.conf import settings
from accounts.views import login_view, register_view, logout_view
from uploader.views import home

from django.contrib.auth.decorators import login_required
from django.views.static import serve

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import HttpResponse,redirect
from uploader.models import File
from .utils import error

def protected_serve(request, path, document_root=None):
    """
    this function is for serving uploaded files and checking link privacy
    """
    try:
        path_fields = path.split('/')
        # Get user
        file_user = path_fields[1]
        # Get file name
        file_name = path_fields[-1]
        # Get file object
        file = File.objects.get(uploader__username=file_user, file_name = file_name)
        # Check privacy settings
        if file.is_public() or (file.uploader == request.user ) or (request.user in file.privacy.shared_with.all()):
            # If allowed to view the file then redirect to the file page
            return serve(request, path, f'{settings.MEDIA_ROOT}/{settings.DRIVE_PATH}')
        else:
            # If the user is not allowed then redirect to error page
            return redirect('error')
    # If the file is not exist then redirect to error page
    except File.DoesNotExist:
        return redirect('error')


def media_serve(request, path, document_root=None):
    """
    this function is for serving Media files
    """
    return serve(request, path, f'{settings.MEDIA_ROOT}/{settings.PROFILE_IMAGES_URL}')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),

    path('login', login_view, name='login'),
    path('register', register_view, name='register'),
    path('logout', logout_view, name='logout'),

    # Account APIs
    path('api/account/', include('accounts.api.urls', 'account_api')),

    # Uploader APIs
    path('api/uploader/', include('uploader.api.urls', 'uploader_api')),

    path('uploader/', include('uploader.urls', namespace='uploader')),
    path('api-auth/', include('rest_framework.urls')),

    # Error url
    path('error', error, name='error'),

    # This Urls is for serving urls in production

    # Serving Uploaded files
    url(r'^{}{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:], settings.DRIVE_PATH), protected_serve),

    # Not Used
    # serving media files
    #url(r'^{}{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:], settings.MEDIA_FILES), media_serve),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
