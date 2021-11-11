from django.shortcuts import render, redirect, reverse
from file.models import File
from folder.models import Folder
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from accounts.models import Account

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
