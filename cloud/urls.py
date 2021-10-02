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

# this function is for checking link privacy
def protected_serve(request, path, document_root=None):
    try:
        path_fields = path.split('/')
        file_user = path_fields[1]
        file_name = path_fields[-1]
        file = File.objects.get(uploader__username=file_user, file_name = file_name)
        if file.is_public() or (file.uploader == request.user ) or (request.user in file.privacy.shared_with.all()):
            return serve(request, path, f'{settings.MEDIA_ROOT}/{settings.DRIVE_PATH}')
        else:
            return redirect('error')
    except File.DoesNotExist:
        return redirect('error')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('error', error, name='error'),

    path('login', login_view, name='login'),
    path('register', register_view, name='register'),
    path('logout', logout_view, name='logout'),
    path('api/account/', include('accounts.api.urls', 'account_api')),

    path('api/uploader/', include('uploader.api.urls', 'uploader_api')),
    path('uploader/', include('uploader.urls', namespace='uploader')),
    path('api-auth/', include('rest_framework.urls')),
    url(r'^{}{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:], settings.DRIVE_PATH), protected_serve),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
