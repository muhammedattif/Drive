from django.shortcuts import HttpResponse, redirect, render
from file.models import File
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.static import serve
from django.http import FileResponse


# Error view
def error(request):
    return render(request, 'error.html')


def protected_serve(request, path, document_root=None):
    """
    this function is for serving uploaded files and checking link privacy
    """
    try:
        #
        # # Get user
        # file_user = path_fields[1]
        #
        # # Get file uploaded day
        # file_uploaded_day = int(path_fields[4])
        #
        # # Get uploaded month
        # file_uploaded_month = int(path_fields[3])
        #
        # # Get uploaded yar
        # file_uploaded_year = int(path_fields[2])
        #
        # # Get file name
        # file_name = path_fields[-1]
        # # Get file object
        # file = File.objects.get(
        #     uploader__username=file_user,
        #     file_name=file_name,
        #     uploaded_at__day=file_uploaded_day,
        #     uploaded_at__month=file_uploaded_month,
        #     uploaded_at__year=file_uploaded_year
        # )
        file_link = path

        file = File.objects.get(privacy__link=file_link)
        # Check privacy settings
        if file.is_public() or (file.uploader == request.user) or (request.user in file.privacy.shared_with.all()):
            # If allowed to view the file then redirect to the file page
            rendered_file = FileResponse(file.file)
            return rendered_file
        else:
            # If the user is not allowed then redirect to error page
            return redirect('error')
    # If the file is not exist then redirect to error page
    except File.DoesNotExist:
        return redirect('error')


@login_required(login_url='login')
def protect_drive_path(request, path):
    """
    this function is for preventing anyone to access drive path
    """
    if not request.user.is_superuser:
        return redirect('error')
    return serve(request, path, f'{settings.MEDIA_ROOT}')


def media_serve(request, path, document_root=None):
    """
    this function is for serving Media files
    """
    return serve(request, path, f'{settings.MEDIA_ROOT}/{settings.PROFILE_IMAGES_URL}')
