from django.shortcuts import render, redirect, reverse
from folder.models import Folder
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
import os, shutil
from django.core.paginator import Paginator
from folder.models import Folder


# Folder View
# This view for a folder to preview its content ( files or child folders )
@login_required(login_url='login')
def folder(request, unique_id=None):
    context = {}
    try:
        if unique_id:
            folder = Folder.objects.get(unique_id=unique_id, user=request.user)
            context['folder'] = folder
            # Child folders
            context['folders'] = folder.folder_set.all()

            # Child files
            files = folder.files.all().filter(trash=None).all()
            paginator = Paginator(files, 10)  # Show 10 files per page.
            page_number = request.GET.get('page')
            files = paginator.get_page(page_number)
            context['files'] = files
        else:
            # Child folders
            context['folders'] = Folder.objects.filter(parent_folder=None, user=request.user)
    except Exception:
        return redirect('error')
    return render(request, 'folder/folder.html', context)


# create folder view
@login_required(login_url='login')
def create_folder(request, unique_id):
    if request.method == 'POST':
        parent_folder_id = unique_id
        child_folder_name = request.POST['child_folder_name']

        if not child_folder_name:
            messages.error(request, "Ops, you forget to enter folder's name.")
            return redirect('home')

        try:
            parent_folder_id = int(parent_folder_id)
        except ValueError:
            pass

        # in case if this folder has a parent folder
        if parent_folder_id:
            parent_folder = Folder.objects.get(user=request.user, unique_id=parent_folder_id)

            # if there is no folders with the same name in this parent folder then create it
            existing_folder, created = Folder.objects.get_or_create(user=request.user, name=child_folder_name,
                                                                    parent_folder=parent_folder)
            if created:
                messages.success(request, f'{child_folder_name} Created Successfully!.')
                return redirect(parent_folder)
            else:
                # in case there is already another folder in this parent folder with the same name
                messages.error(request, 'A folder with the same name already exists.')
                return redirect(parent_folder)
        else:

            existing_folder, created = Folder.objects.get_or_create(user=request.user, name=child_folder_name,
                                                                    parent_folder=None)

            if created:
                messages.success(request, f'{child_folder_name} Created Successfully!.')
                return redirect('home')
            else:
                # in case there is already another folder in this parent folder with the same name
                messages.error(request, 'A folder with the same name already exists.')
                return redirect('home')

    messages.error(request, 'Something went wrong!.')
    return redirect('home')


# delete folder View
@login_required(login_url='login')
def delete_folder(request, unique_id):
    user = request.user
    try:
        folder = Folder.objects.get(user=user, unique_id=unique_id)

        # This code is to know to which page the user is going to be redirect
        folder_name = folder.name
        if folder.parent_folder is not None:
            redirect_path = folder.parent_folder.get_absolute_url()
        else:
            redirect_path = '/'

        # delete folder dir from physical storage
        if folder.parent_folder:

            folder_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(folder.user.unique_id),
                folder.parent_folder.get_folder_tree_as_dirs(),
                folder.name)

        else:
            folder_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(folder.user.unique_id),
                folder.name)

        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

        # Delete folder from db
        folder.delete()

        messages.success(request, f'{folder_name} deleted successfully!.')
        return redirect(redirect_path)

    except Exception:
        return redirect('error')
