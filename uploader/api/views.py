from django.shortcuts import render
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from uploader.models import File, Folder
import json

# Create your views here.

# this function create folder tree if not exist and return directory object
def create_folder_tree_if_not_exist(folder_tree, user):

    parent_folder = None

    folder_tree = folder_tree.split('/')
    folder_tree = list(filter(None, folder_tree))

    base_folder_name = folder_tree[0]
    home_folders_names = Folder.objects.filter(user=user, parent_folder=None).values_list('name', flat=True)

    for index, folder_name in enumerate(folder_tree):
        # this check is because the home directory does not have a parent folder
        if index == 0:
            if base_folder_name not in home_folders_names:
                folder = Folder.objects.create(user=user, name=folder_name)
            else:
                folder = Folder.objects.get(user=user, name=folder_name, parent_folder=None)
            # set current folder as a parent to the next folder
            parent_folder = folder
        else:
            # if not exist create new one
            if folder_name not in parent_folder.folder_set.all().values_list('name', flat=True):
                folder = Folder.objects.create(user=user, name=folder_name, parent_folder=parent_folder)
            else:
                # get folder if exist
                folder = Folder.objects.get(user=user, name=folder_name, parent_folder=parent_folder)

            # set current folder as a parent to the next folder
            parent_folder = folder

    # return end of tree folder id
    return parent_folder

# Upload File
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request, format=None):
    content = {}
    links = []

    # if request has file
    if bool(request.FILES.get('file', False)) == True:

        user = request.user
        uploaded_files = request.FILES.getlist('file')

        # get data from post request
        folder_tree = request.POST['folder_tree'] if 'folder_tree' in request.POST else None
        directory_id = request.POST['directory_id'] if 'directory_id' in request.POST else None
        privacy = request.POST['privacy'] if 'privacy' in request.POST else None

        files_size = 0

        # sum all files sizes
        for file in uploaded_files:
            files_size += file.size

        # check if the user is allowed to upload files with these size or his limit reached
        if user.drive_settings.is_allowed_to_upload_files(files_size):

            # check request params

            # if folder tree passed then get or create it
            if folder_tree:
                parent_folder = create_folder_tree_if_not_exist(folder_tree, user)

            # if directory id passed then upload file to this directory
            elif directory_id:
                try:
                    parent_folder = Folder.objects.get(id=directory_id, user=user)
                except Folder.DoesNotExist:
                    content['message'] = 'Directory Not found.'
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)
            else:
                # if no folder tree or directory id then upload to base folder
                parent_folder = None

            # get all files in the request and upload it
            for file in uploaded_files:
                uploaded_file = file
                file_name = uploaded_file.name
                file_size = uploaded_file.size
                file_category = get_file_cat(uploaded_file)
                file_type = uploaded_file.content_type

                try:

                    file = File.objects.create(
                         uploader=user, file_name=file_name,
                         file_size=file_size, file_type=file_type,
                         file_category=file_category,
                         file=uploaded_file, parent_folder=parent_folder
                    )
                    # if privacy parameter passed then set it, if not then the default is 'private'
                    if privacy:
                        file.privacy.option = privacy
                        file.privacy.save()

                except Exception:
                    content['message'] = 'Something went wrong!'
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)

                if not parent_folder:
                    directory_id = ''

                else:
                    directory_id = parent_folder.id

                content = {
                    'uploader': file.uploader.email,
                    'file_name': file.file_name,
                    'file_id': file.pk,
                    'file_link': file.get_url(),
                    'file_size': file.file_size,
                    'file_type': file.file_type,
                    'file_category': file.file_category,
                    'uploaded_at': file.uploaded_at,
                    'directory_id': directory_id
                }
                links.append(content)
        else:
            content['message'] = 'Limit Exceeded!'
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    else:
        content['message'] = 'No file to upload.'
        return Response(content, status=status.HTTP_404_NOT_FOUND)

    return Response({"files": links})

# Delete File
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete(request, id):
    content = {}
    user = request.user
    try:
        file = File.objects.get(pk=id, uploader=user)
        file.delete()
        content['message'] = 'File Deleted Successfully!'
    except File.DoesNotExist:
        content['message'] = 'File Does not Exists!'
    return Response(content)


# Upload File
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_folder_tree(request, format=None):

    user = request.user

    folder_tree = request.POST['folder_tree']

    parent_folder = create_folder_tree_if_not_exist(folder_tree, user)

    content = {
    'message': 'Folders Created Successfully!',
    'directory_id': parent_folder.id
    }
    return Response(content)

# Upload File
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_folder(request, format=None):
    content = {}
    user = request.user

    folder_tree = request.POST['folder_tree']
    folder_tree = folder_tree.split('/')
    # is for cleaning folder tree from '' spaces
    folder_tree = list(filter(None, folder_tree))


    home_folders_names = Folder.objects.filter(user=user, parent_folder=None).values_list('name', flat=True)
    base_folder_name = folder_tree[0]

    if base_folder_name in home_folders_names:
        parent_folder = Folder.objects.get(user=user, name=base_folder_name)
        if len(folder_tree) > 1:
            for index, folder_name in enumerate(folder_tree[1:]):
                try:
                    folder = Folder.objects.get(user=user, name=folder_name, parent_folder=parent_folder)
                    parent_folder = folder

                except Exception as e:
                    content['message'] = 'Folder does not exist.'
                    return Response(content)

            folder.delete()
            content['message'] = 'Folder Removed Successfully!'
            return Response(content)
        else:
            parent_folder.delete()
            content['message'] = 'Folder Removed Successfully!'
            return Response(content)
    else:
        content['message'] = 'Folder does not exist.'


    return Response(content)

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
