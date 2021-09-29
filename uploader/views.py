from django.shortcuts import render, redirect, reverse
from uploader.models import File, Trash, Folder
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

# Create your views here.
@login_required(login_url='login')
def home(request):
    print(dir(request.user.drive_settings))
    if not request.user.is_authenticated:
        return redirect('login')
    try:
        files = File.objects.filter(uploader=request.user, trash = None, parent_folder = None)
    except Exception as e:
        files = File.objects.filter(uploader=request.user)

    try:
        folders = Folder.objects.filter(parent_folder=None, user=request.user)
    except Exception as e:
         folders = None

    context = {
    'files':files,
    'folders': folders
    }

    return render(request, 'uploader/home.html', context)


def folder(request, id=None):
    context = {}
    if id:
        folder = Folder.objects.get(id=id, user=request.user)
        context['folder'] = folder
        context['folders'] = folder.folder_set.all()
        context['files'] = folder.files.all().filter(trash = None)
    else:
        context['folders'] = Folder.objects.filter(parent_folder=None, user=request.user)

    return render(request, 'uploader/folder.html', context)


@login_required(login_url='login')
def upload(request):
    if request.method == 'POST':
        files_links = []
        user = request.user

        uploaded_files = request.FILES.getlist('file')

        for file in uploaded_files:

            file_name = file.name
            file_size = file.size
            file_category = get_file_cat(file)
            file_type = file.content_type

            try:
                file = File.objects.create(uploader=user, file_name=file_name, file_size=file_size, file_type=file_type,
                                           file_category=file_category, file=file)
                folder_id = request.POST['folder_id']
                if folder_id:
                    folder = Folder.objects.get(id=folder_id)
                    folder.files.add(file)
            except Exceptio as e:
                pass

            files_links.append(file.get_url())

        context = {
          'files_links': files_links
        }

        return JsonResponse(json.dumps(context), content_type="application/json",safe=False)

    return render(request, 'uploader/upload.html')

@login_required(login_url='login')
def create_folder(request, id):

    if request.method == 'POST':
        parent_folder_id = id
        child_folder_name = request.POST['child_folder_name']
        if parent_folder_id:
            parent_folder = Folder.objects.get(user=request.user, id=parent_folder_id)
            Folder.objects.create(user=request.user, name=child_folder_name, parent_folder = parent_folder)
            return redirect('/uploader/folder/{}'.format(parent_folder_id))
        else:
            Folder.objects.create(user=request.user, name=child_folder_name)
            return redirect('home')

    return redirect('home')

@login_required(login_url='login')
def filter(request, cat):
    context = {}
    if cat == 'all':
        files = File.objects.filter(uploader=request.user, trash=None, parent_folder = None)
        context['files'] = files

    elif cat == 'folders':
        try:
            folders = Folder.objects.filter(parent_folder=None, user=request.user)
        except Exception as e:
            folders = None
        context['folders'] = folders
    else:
        files = File.objects.filter(uploader=request.user, file_category = cat, trash = None, parent_folder = None)
        context['files'] = files

    return render(request, 'uploader/home.html', context)


@login_required(login_url='login')
def get_trashed_files(request):
    context = {}
    trashed_files = Trash.objects.filter(user=request.user)
    context['trashed_files'] = trashed_files
    return render(request, 'uploader/trashed_files.html', context)

@login_required(login_url='login')
def move_to_trash(request, id):
    context = {}
    try:
        file = File.objects.get(pk=id, uploader=request.user)
        Trash.objects.create(user=file.uploader, file=file)
        context['message'] = 'File Trashed Successfully!'
    except File.DoesNotExist:
        context['message'] = 'File Does not Exists!'
    return redirect('home')

@login_required(login_url='login')
def delete(request, id):
    context = {}
    try:
        file = File.objects.get(pk=id, uploader=request.user)
        file.delete()
    except File.DoesNotExist:
        context['message'] = 'File Does not Exists!'
    return redirect('/uploader/trash')


@login_required(login_url='login')
def recover(request, id):

    try:
        trashed_file = Trash.objects.get(file__id=id, user=request.user)
        trashed_file.delete()
    except Trash.DoesNotExist:
        return redirect('/uploader/trash')
    return redirect('/uploader/trash')


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
