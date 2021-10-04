from django.shortcuts import render, redirect, reverse
from uploader.models import File, Trash, Folder, FilePrivacy
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
from django.contrib import messages
from uploader.forms import FilePrivacyForm
from accounts.models import Account


# Home Page View
@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get files of home dir if exist
    try:
        files = File.objects.filter(uploader=request.user, trash = None, parent_folder = None)
    except Exception:
        files = File.objects.filter(uploader=request.user)

    # Get folders of home dir if exist
    try:
        folders = Folder.objects.filter(parent_folder=None, user=request.user)
    except Exception:
         folders = None

    context = {
    'files':files,
    'folders': folders
    }

    return render(request, 'uploader/home.html', context)


# Folder View
# This view for a folder to preview its content ( files or child folders )
@login_required(login_url='login')
def folder(request, id=None):
    context = {}
    try:
        if id:
            folder = Folder.objects.get(id=id, user=request.user)
            context['folder'] = folder
            context['child_folders'] = folder.folder_set.all()
            context['child_files'] = folder.files.all().filter(trash = None)
        else:
            context['child_folders'] = Folder.objects.filter(parent_folder=None, user=request.user)
    except Exception:
        return redirect('error')

    return render(request, 'uploader/folder.html', context)


# Change file settings view
@login_required(login_url='login')
def file_settings(request, id):
    try:
        file_privacy_settings = FilePrivacy.objects.get(file__id=id, file__uploader=request.user)
    except FilePrivacy.DoesNotExist:
        return redirect('error')

    if request.method == 'POST':

        shared_with_users = request.POST['users']
        shared_with_users = shared_with_users.replace('\r\n', ' ')
        shared_with_users = shared_with_users.split(' ')


        form = FilePrivacyForm(request.POST, instance=file_privacy_settings)

        if form.is_valid():
            form = form.save(commit=False)
            if len(shared_with_users) > 0:
                invalid_user = False
                file_privacy_settings.shared_with.clear()
                for user in shared_with_users:
                    if user:
                        try:
                            user = Account.objects.get(email=user)
                            file_privacy_settings.shared_with.add(user)
                        except Account.DoesNotExist:
                            invalid_user = True

                file_privacy_settings.save()
            form.save()

            if invalid_user:
                messages.error(request, 'Saved!, But It seems that you shared this file with an email address that is not associated with any user.')
            else:
                messages.success(request, f'{file_privacy_settings.file.file_name} sharing settings updated successfully!')
    context = {
    'form': FilePrivacyForm(instance=file_privacy_settings),
    'file': file_privacy_settings.file,
    'file_settings': file_privacy_settings
    }

    return render(request, 'uploader/file_settings.html', context)


# upload file view
@login_required(login_url='login')
def upload(request):
    if request.method == 'POST':
        # get current user
        user = request.user
        # get uploaded files
        uploaded_files = request.FILES.getlist('file')

        # Get parent folder ID
        folder_id = request.POST['folder_id']

        files_links = []
        files_size = 0

        # sum all the uploaded files sizes
        for file in uploaded_files:
            files_size += file.size

        # check if the user does not reached his upload limit
        if user.drive_settings.is_allowed_to_upload_files(files_size):
            for file in uploaded_files:
                file_name = file.name
                file_size = file.size
                file_category = get_file_cat(file)
                file_type = file.content_type

                try:
                    if folder_id:
                        parent_folder = Folder.objects.get(id=folder_id)
                    else:
                        parent_folder = None

                    file = File.objects.create(uploader=user, file_name=file_name, file_size=file_size, file_type=file_type,
                                               file_category=file_category, file=file, parent_folder=parent_folder)
                except Folder.DoesNotExist:
                    context = {
                        'message': 'Destination Folder Not found!'
                    }
                    return JsonResponse(context, status=400, content_type="application/json", safe=False)

                files_links.append(file.get_url())

            context = {
              'files_links': files_links
            }
            return JsonResponse(context,content_type="application/json",safe=False)
        # An error will be raised if the used reached upload limit
        else:
            context = {
              'message': 'Limit Exceeded!'
            }
            return JsonResponse(context, status=400, content_type="application/json",safe=False)

    return redirect('home')

# create folder view
@login_required(login_url='login')
def create_folder(request, id):
    if request.method == 'POST':
        parent_folder_id = id
        child_folder_name = request.POST['child_folder_name']
        # in case if this folder has a parent folder
        if parent_folder_id:
            parent_folder = Folder.objects.get(user=request.user, id=parent_folder_id)

            # Get all child folders of this parent folder
            parent_folder_children_names = parent_folder.folder_set.all().values_list('name', flat=True)

            # in case there is already another folder in this parent folder with the same name
            if child_folder_name in parent_folder_children_names:
                messages.error(request, 'A folder with the same name already exists.')
                return redirect('/uploader/folder/{}'.format(parent_folder_id))
            else:
                # in case there is no folders with the same name in this parent folder then create it
                Folder.objects.create(user=request.user, name=child_folder_name, parent_folder = parent_folder)
                messages.success(request, f'{child_folder_name} Created Successfully!.')
                return redirect('/uploader/folder/{}'.format(parent_folder_id))
        else:
            # get all folders names in home directory
            home_folder_set_names = Folder.objects.filter(user=request.user, parent_folder=None).values_list('name', flat=True)
            # in case this folder does not have a parent folder then create it in home directory
            if child_folder_name in home_folder_set_names:
                messages.error(request, 'A folder with the same name already exists.')
                return redirect('home')
            else:
                # in case there is no folders with the same name in this parent folder then create it
                Folder.objects.create(user=request.user, name=child_folder_name)
                messages.success(request, f'{child_folder_name} Created Successfully!.')
                return redirect('home')
    messages.error(request, 'Something went wrong!.')
    return redirect('home')


# delete folder View
@login_required(login_url='login')
def delete_folder(request, id):
    user = request.user
    try:
        folder = Folder.objects.get(user=user, id=id)

        # This code is to know to which page the user is going to be redirect
        folder_name = folder.name
        if folder.parent_folder is not None:
            parent_folder_id = folder.parent_folder.id
            redirect_path = '/uploader/folder/{}'.format(parent_folder_id)
        else:
            redirect_path = '/uploader'
        # Delete folder
        folder.delete()

        messages.success(request, f'{folder_name} deleted successfully!.')
        return redirect(redirect_path)

    except Exception:
        return redirect('error')



# Filter files based on category view
@login_required(login_url='login')
def filter(request, cat):
    """
    This function is to filter files based on category
    """
    context = {}
    if cat == 'all':
        files = File.objects.filter(uploader=request.user, trash=None, parent_folder = None)
        context['files'] = files

    elif cat == 'folders':
        try:
            folders = Folder.objects.filter(parent_folder=None, user=request.user)
        except Exception:
            folders = None
        context['folders'] = folders
    else:
        files = File.objects.filter(uploader=request.user, file_category = cat, trash = None, parent_folder = None)
        context['files'] = files

    return render(request, 'uploader/home.html', context)

# Trashed files view
@login_required(login_url='login')
def get_trashed_files(request):
    context = {}
    trashed_files = Trash.objects.filter(user=request.user)
    context['trashed_files'] = trashed_files
    return render(request, 'uploader/trashed_files.html', context)

# Move file to trash view
@login_required(login_url='login')
def move_to_trash(request, id):
    file = None
    try:
        file = File.objects.get(pk=id, uploader=request.user)
        Trash.objects.create(user=file.uploader, file=file)
        messages.success(request, f'{file.file_name} moved to trash.')
    except File.DoesNotExist:
        messages.error(request, 'File Does not Exists!')
    if file.parent_folder is not None:
        return redirect(f'/uploader/folder/{file.parent_folder.id}')
    return redirect('home')

# Delete file view
@login_required(login_url='login')
def delete_file(request, id):
    try:
        file = File.objects.get(pk=id, uploader=request.user)
        file.delete()
        messages.success(request, f'{file.file_name} was permanently deleted.')
    except File.DoesNotExist:
        messages.error(request, 'File Does not Exists!')
    return redirect('/uploader/trash')

# Recover file view
@login_required(login_url='login')
def recover(request, id):
    try:
        trashed_file = Trash.objects.get(file__id=id, user=request.user)
        trashed_file.delete()
        messages.success(request, f'{trashed_file.file.file_name} was recovered')
    except Trash.DoesNotExist:
        messages.error(request, 'File Does not Exists!')
        return redirect('/uploader/trash')
    return redirect('/uploader/trash')

# Function for categorising files
def get_file_cat(file):
    docs_ext =  ['pdf','doc','docx','xls','ppt','txt']
    if file.content_type.split('/')[0] == 'image':
        return 'images'
    elif file.content_type.split('/')[0] == 'audio' or file.content_type.split('/')[0] == 'video':
        return 'media'
    elif file.name.split('.')[-1] in docs_ext or file.content_type.split('/')[0] == 'text':
        return 'docs'
    else:
        return 'other'
