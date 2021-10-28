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
from uploader.views import home, download
import datetime
from django.shortcuts import HttpResponse,redirect, render

from .utils import error, protect_drive_path, protected_serve



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
    path('link/<str:path>', protected_serve),

    # Download file
    path('link/<str:file_link>/download', download, name='download'),

    # Protect Drive path
    url(r'^{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:]), protect_drive_path),

    # Not Used
    # serving media files
    #url(r'^{}{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:], settings.MEDIA_FILES), media_serve),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
