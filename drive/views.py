from django.shortcuts import render, redirect, reverse
from file.models import File
from folder.models import Folder
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from accounts.models import Account
from .models import DriveSettings
from .forms import PrivacySettingsForm
from django.contrib import messages

import subprocess


# Home Page View
@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get files of home dir if exist
    try:
        files = File.objects.filter(uploader=request.user, trash=None, parent_folder=None).select_related('privacy')
    except Exception:
        files = File.objects.filter(uploader=request.user).select_related('privacy')

    # Get folders of home dir if exist
    try:
        folders = Folder.objects.filter(parent_folder=None, user=request.user)
    except Exception as e:
        print(e)
        folders = None

    paginator = Paginator(files, 10)  # Show 10 files per page.
    page_number = request.GET.get('page')
    files = paginator.get_page(page_number)

    context = {
        'files': files,
        'folders': folders
    }

    return render(request, 'drive/home.html', context)


# Filter files based on category view
@login_required(login_url='login')
def filter(request, cat):
    """
    This function is to filter files based on category
    """
    context = {}
    files = None
    if cat == 'all':
        files = File.objects.filter(uploader=request.user, trash=None, parent_folder=None).select_related('privacy')

    elif cat == 'folders':
        try:
            folders = Folder.objects.filter(parent_folder=None, user=request.user)
        except Exception:
            folders = None
        context['folders'] = folders
    else:
        files = File.objects.filter(uploader=request.user, file_category=cat, trash=None, parent_folder=None).select_related('privacy')

    if files:
        paginator = Paginator(files, 10)  # Show 10 files per page.
        page_number = request.GET.get('page')
        files = paginator.get_page(page_number)
        context['files'] = files

    return render(request, 'drive/home.html', context)

# privacy settings view
@login_required(login_url='login')
def privacy_settings(request):

    try:
        privacy_settings = DriveSettings.objects.get(user=request.user)
    except DriveSettings.DoesNotExist:
        return redirect('error')

    if request.method == 'POST':
        print(request.POST)
        form = PrivacySettingsForm(request.POST, instance=privacy_settings)

        if form.is_valid():
            form.save()
            messages.success(request,'File permissions updated successfully')
        else:
            messages.error(request,
                            'Something went wrong. Try again later!.')

    context = {
        'form': PrivacySettingsForm(instance=privacy_settings),
        'default_upload_privacy': privacy_settings.default_upload_privacy
    }

    return render(request, 'drive/privacy_settings.html', context)