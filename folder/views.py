from django.shortcuts import render, redirect, reverse
from folder.models import Folder
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.contrib import messages
import os, shutil
from django.core.paginator import Paginator
from folder.models import Folder
import string
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from django.http import FileResponse, HttpResponse


# Folder View
# This view for a folder to preview its content ( files or child folders )
@login_required(login_url='login')
def folder(request, unique_id=None):
    context = {}
    if unique_id:
        folder = Folder.objects.filter(unique_id=unique_id).first()
        if not folder:
            return redirect('error')

        shared_object, is_shared = folder.is_shared_with(request.user)
        if not is_shared and folder.user != request.user:
            return redirect('error')

        context['folder'] = folder
        # Child folders
        context['folders'] = folder.sub_folders.all().select_related('parent_folder')

        # Child files
        files = folder.files.filter(trash=None).select_related('privacy')
        paginator = Paginator(files, 10)  # Show 10 files per page.
        page_number = request.GET.get('page')
        files = paginator.get_page(page_number)
        context['files'] = files
    else:
        # Child folders
        context['folders'] = Folder.objects.filter(parent_folder=None, user=request.user)

    if folder.user != request.user:
        context['shared_object'] = shared_object
        return render(request, 'shared_content.html', context)

    return render(request, 'folder/folder.html', context)


# create folder view
@login_required(login_url='login')
def create_folder(request, unique_id):

    if request.method == 'POST':
        parent_folder_id = unique_id
        child_folder_name = request.POST['child_folder_name']

        # check if the folder name is not None
        if len(child_folder_name.translate({ord(c): None for c in string.whitespace})) == 0 :
            messages.error(request, "Ops, you forget to enter folder's name.")
            return redirect('home')

        try:
            parent_folder_id = int(parent_folder_id)
        except ValueError:
            pass

        # in case if this folder has a parent folder
        if parent_folder_id:
            parent_folder = Folder.objects.get(user=request.user, unique_id=parent_folder_id)

            if len(parent_folder.get_folder_tree()) >= settings.SUB_FOLDERS_LIMIT:
                messages.error(request, f'{child_folder_name} cannot be created, sub folders limit is {settings.SUB_FOLDERS_LIMIT}!.')
                return redirect(parent_folder)

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
@permission_required('folder.delete_folder', raise_exception=True)
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

# Download folder View
@login_required(login_url='login')
@permission_required('folder.can_download_folder', raise_exception=True)
def download_folder(request, unique_id):

    folder = Folder.objects.get(user=request.user, unique_id=unique_id)
    folder_tree = folder.get_folder_tree_as_dirs()

    user = request.user
    folder_to_compress = Path(os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(user.unique_id), folder_tree))

    path_to_archive_in_os = Path(
        os.path.join(settings.MEDIA_ROOT, settings.COMPRESS_PATH, f"{str(folder.name)}{'.zip'}"))

    with ZipFile(
            path_to_archive_in_os,
            mode="w",
            compression=ZIP_DEFLATED
    ) as zip:
        for file in folder_to_compress.rglob("*"):
            relative_path = file.relative_to(folder_to_compress)
            print(f"Packing {file} as {relative_path}")
            zip.write(file, arcname=relative_path)

    response = FileResponse(open(path_to_archive_in_os, 'rb'), as_attachment=True)
    response['Content-Disposition'] = 'attachment; filename={}'.format(folder.name + '.zip')
    return response


# Rename folder View
@login_required(login_url='login')
@permission_required('folder.can_rename_folder', raise_exception=True)
def rename_folder(request, unique_id):
    if request.method != 'POST':
        return redirect('error')

    folder_new_name = request.POST['folder_new_name']
    user = request.user

    try:
        current_folder = Folder.objects.get(user=user, unique_id=unique_id)
        folder_old_name = current_folder.name

        # This code is to know to which page the user is going to be redirect
        if current_folder.parent_folder is not None:
            redirect_path = current_folder.parent_folder.get_absolute_url()
        else:
            redirect_path = '/'

        # delete folder dir from physical storage

        if current_folder.parent_folder:

            folder_old_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_folder.parent_folder.get_folder_tree_as_dirs(),
                current_folder.name)

            folder_new_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_folder.parent_folder.get_folder_tree_as_dirs(),
                folder_new_name)

        else:
            folder_old_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_folder.name)

            folder_new_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                folder_new_name)

        # Query the DB to check if there is a folder with the new name
        is_folder_exists_in_db = Folder.objects.filter(user=user, name=folder_new_name, parent_folder=current_folder.parent_folder).exists()

        if os.path.exists(folder_new_path) or is_folder_exists_in_db:
            messages.error(request, 'Folder with this name is already exists.')
            return redirect(redirect_path)

        if os.path.exists(folder_old_path):

            # Rename folder on the physical disk
            try:
                os.rename(folder_old_path, folder_new_path)
            except:
                messages.error(request, 'Cannot rename folder on the physical storage!')
                return redirect(redirect_path)

        try:
            # Rename folder in DB
            current_folder.name = folder_new_name
            current_folder.save(update_fields=['name'])
        except:
            os.rename(folder_new_path, folder_old_path)
            messages.error(request, 'Cannot rename the folder!')
            return redirect(redirect_path)


        messages.success(request, f'{folder_old_name} renamed successfully to {current_folder.name}.')
        return redirect(redirect_path)

    except Exception:
        return redirect('error')
