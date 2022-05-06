# Standard library
import time
import os

# Django
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core import exceptions
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, reverse
from django.conf import settings

# Accounts app
from accounts.models import Account

# Activities app
from activity.models import Activity

# Folders App
from folder.models import Folder

# Local Django
from file.forms import FilePrivacyForm
from file.models import File, FilePrivacy, FileQuality, Trash
from file.utils import get_file_cat
from .models import SharedObject
from .utils import get_supported_qualities


# upload file view
@login_required(login_url='login')
def upload(request):
    if not request.method == 'POST':
        return redirect('home')

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
    if not user.drive_settings.is_allowed_to_upload_files(files_size):
        # An error will be raised if the used reached upload limit
        context = {
            'message': 'Limit Exceeded!'
        }
        return JsonResponse(context, status=507, content_type="application/json", safe=False)

    for file in uploaded_files:
        file_name = file.name

        # Don't upload files that doesn't has extension
        if '.' not in file_name:
            context = {
                'message': 'Invalid File!'
            }
            return JsonResponse(context, status=400, content_type="application/json", safe=False)

        size = file.size
        category = get_file_cat(file)
        type = file.content_type

        try:
            if folder_id:
                parent_folder = Folder.objects.get(unique_id=folder_id)
            else:
                parent_folder = None
            file = File.objects.create(user=user, name=file_name, size=size,
                                       type=type,
                                       category=category, file=file, parent_folder=parent_folder)
        except Folder.DoesNotExist:
            context = {
                'message': 'Destination Folder Not found!'
            }
            return JsonResponse(context, status=404, content_type="application/json", safe=False)
        except exceptions.SuspiciousFileOperation:
            context = {
                'message': 'File name is too large!'
            }
            return JsonResponse(context, status=400, content_type="application/json", safe=False)
        except FileNotFoundError:
            context = {
                'message': 'Folder is corrupted!'
            }
            return JsonResponse(context, status=500, content_type="application/json", safe=False)

        files_links.append(file.get_url())

    context = {
        'files_links': files_links
    }
    return JsonResponse(context, content_type="application/json", safe=False)




# Trashed files view
@login_required(login_url='login')
@permission_required('file.can_add_files_to_trash', raise_exception=True)
def get_trashed_files(request):
    context = {}
    trashed_files = Trash.objects.filter(user=request.user).select_related('file__privacy')
    paginator = Paginator(trashed_files, 10)  # Show 10 files per page.
    page_number = request.GET.get('page')
    trashed_files = paginator.get_page(page_number)
    context['trashed_files'] = trashed_files
    return render(request, 'file/trashed_files.html', context)


# Move file to trash view
@login_required(login_url='login')
@permission_required('file.can_add_files_to_trash', raise_exception=True)
def move_to_trash(request, unique_id):
    file = None
    try:
        file = File.objects.get(unique_id=unique_id, user=request.user)
        Trash.objects.create(user=file.user, file=file)
        file.activities.create(
            activity_type=Activity.TRASH_FILE,
            user=request.user,
            object_name=file.name
        )
        messages.success(request, f'{file.name} moved to trash.')
    except File.DoesNotExist:
        messages.error(request, 'File Does not Exists!')
    if file.parent_folder is not None:
        return redirect(file.parent_folder)
    return redirect('home')


# Delete file view
@login_required(login_url='login')
@permission_required('file.delete_file', raise_exception=True)
def delete_file(request, unique_id, quality=None):
    try:
        file = File.objects.get(unique_id=unique_id, user=request.user)
        if quality:
            converted_file = file.qualities.get(quality=quality).converted_file
            file = File.objects.get(unique_id=converted_file.unique_id)

        file.delete()
        messages.success(request, f'{file.name} was permanently deleted.')
    except File.DoesNotExist:
        messages.error(request, 'File Does not Exists!')
    if quality:
        return HttpResponseRedirect(reverse('file:file_settings', kwargs={'unique_id': unique_id}))

    return redirect('/file/trash')


# Recover file view
@login_required(login_url='login')
@permission_required('file.delete_file', raise_exception=True)
def recover(request, unique_id):
    try:
        trashed_file = Trash.objects.get(file__unique_id=unique_id, user=request.user)
        trashed_file.delete()
        trashed_file.file.activities.create(
            activity_type=Activity.RECOVER_FILE,
            user=request.user,
            object_name=trashed_file.file.name
        )
        messages.success(request, f'{trashed_file.file.name} was recovered')
    except Trash.DoesNotExist:
        messages.error(request, 'File Does not Exists!')
        return redirect('/file/trash')
    return redirect('/file/trash')


# download file view
@login_required(login_url='login')
@permission_required('file.can_download_file', raise_exception=True)
def download(request, file_link):
    try:
        file = File.objects.get(privacy__link=file_link)

        # Check privacy settings
        if file.is_public() or (file.user == request.user) or (request.user in file.privacy.accessed_by.all()) or file.is_shared_with(request.user)[1]:
            response = FileResponse(file.file, as_attachment=True)
            response['Content-Disposition'] = f'attachment; filename="{file.name}"'
            return response
        else:
            return redirect('error')

    except File.DoesNotExist:
        return redirect('error')


# Rename file View
@login_required(login_url='login')
@permission_required('file.can_rename_file', raise_exception=True)
def rename_file(request, unique_id):

    if request.method != 'POST':
        return redirect('error')

    file_new_name = request.POST['file_new_name']
    user = request.user

    try:
        current_file = File.objects.get(user=user, unique_id=unique_id)
        file_old_name = current_file.name

        # This code is to know to which page the user is going to be redirect
        if current_file.parent_folder is not None:
            redirect_path = current_file.parent_folder.get_absolute_url()
        else:
            redirect_path = '/'

        # delete folder dir from physical storage

        if current_file.parent_folder:

            file_old_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_file.parent_folder.get_folder_tree_as_dirs(),
                current_file.name)

            file_new_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_file.parent_folder.get_folder_tree_as_dirs(),
                file_new_name)

            file_db_new_path = os.path.join(
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_file.parent_folder.get_folder_tree_as_dirs(),
                file_new_name)

        else:
            file_old_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                current_file.name)

            file_new_path = os.path.join(
                settings.MEDIA_ROOT,
                settings.DRIVE_PATH,
                str(user.unique_id),
                file_new_name)

            file_db_new_path = os.path.join(
                settings.DRIVE_PATH,
                str(user.unique_id),
                file_new_name)

        if file_new_name == file_old_name:
            messages.error(request, 'File new name is the same as the old one :)')
            return redirect(redirect_path)

        # Query the DB to check if there is a file with the new name
        is_file_exists_in_db = File.objects.filter(user=user, name=file_new_name, parent_folder=current_file.parent_folder).exists()

        if os.path.exists(file_new_path) or is_file_exists_in_db:
            messages.error(request, 'File with this name is already exists.')
            return redirect(redirect_path)

        if os.path.exists(file_old_path):

            # Rename file on the physical disk
            try:
                os.rename(file_old_path, file_new_path)
            except:
                messages.error(request, 'Cannot rename file on the physical storage!')
                return redirect(redirect_path)

        try:
            # Rename file in DB
            current_file.name = file_new_name
            current_file.file.name = file_db_new_path
            current_file.save(update_fields=['name', 'file'])
        except Exception as e:
            os.rename(file_new_path, file_old_path)
            messages.error(request, 'Cannot rename the file!')
            return redirect(redirect_path)


        messages.success(request, f'{file_old_name} renamed successfully to {current_file.name}.')
        return redirect(redirect_path)

    except Exception as e:
        print(e)
        return redirect('error')


# Change file settings view
@login_required(login_url='login')
def file_settings(request, unique_id):
    try:
        file_privacy_settings = FilePrivacy.objects.get(file__unique_id=unique_id, file__user=request.user)
    except FilePrivacy.DoesNotExist:
        return redirect('error')

    if request.method == 'POST':

        accessed_by_users = request.POST['users']
        accessed_by_users = accessed_by_users.replace('\r\n', ' ')
        accessed_by_users = accessed_by_users.split(' ')

        form = FilePrivacyForm(request.POST, instance=file_privacy_settings)

        if form.is_valid():
            form = form.save(commit=False)
            if len(accessed_by_users) > 0:
                invalid_user = False
                file_privacy_settings.accessed_by.clear()
                for user in accessed_by_users:
                    if user:
                        try:
                            user = Account.objects.get(email=user)
                            file_privacy_settings.accessed_by.add(user)
                        except Account.DoesNotExist:
                            invalid_user = True
            form.save()

            if invalid_user:
                messages.error(request,
                               'Saved!, But It seems that you shared this file with an email address that is not associated with any user.')
            else:
                messages.success(request,
                                 f'{file_privacy_settings.file.name} sharing settings updated successfully!')

    file_type = file_privacy_settings.file.type.split('/')[0]

    context = {
        'form': FilePrivacyForm(instance=file_privacy_settings),
        'file': file_privacy_settings.file,
        'file_type': file_type,
        'file_settings': file_privacy_settings
    }
    if file_type == 'video' and not file_privacy_settings.file.properties.converted:

        video_quality = file_privacy_settings.file.properties.quality
        supported_qualities = get_supported_qualities(video_quality)
        file_converted_qualities = file_privacy_settings.file.qualities.values_list('quality', flat=True)
        not_converted_qualities = list(set(supported_qualities) - set(file_converted_qualities))

        context['supported_qualities'] =  supported_qualities
        context['not_converted_qualities'] = not_converted_qualities
        context['converted_qualities'] = file_privacy_settings.file.qualities.all()

    return render(request, 'file/file_settings.html', context)

@login_required(login_url='login')
@permission_required('file.can_convert_media_files', raise_exception=True)
def convert_file_quality(request, unique_id, quality):

    from file.tasks import async_convert_video_quality

    async_convert_video_quality.delay(unique_id, quality, request.user.id)
    time.sleep(1)

    messages.success(request, 'Video quality is being processed and will be available soon.')

    return HttpResponseRedirect(reverse('file:file_settings', kwargs={'unique_id': unique_id}))


def stream(request):
    return render(request, 'file/stream.html')

def shared_with(request, unique_id):
    file = File.objects.filter(unique_id=unique_id, user=request.user).first()

    if not file:
        return redirect('error')

    shared_objects = SharedObject.objects.filter(object_id=file.id, content_type__model='file', shared_by=request.user)
    context = {
      'shared_objects': shared_objects
    }
    return render(request, 'shared_with_users_list.html', context)
