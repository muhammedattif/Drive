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

    # split folder tree and convert it to a list of folders
    folder_tree = folder_tree.split('/')
    # remove none or empty values form the list
    folder_tree = list(filter(None, folder_tree))

    # first folder in folder tree
    base_folder_name = folder_tree[0]

    # get a list of all folders in base directory (Home)
    home_folders_names = Folder.objects.filter(user=user, parent_folder=None).values_list('name', flat=True)

    for index, folder_name in enumerate(folder_tree):
        # this check is because the home directory does not have a parent folder
        if index == 0:
            # check if the first folder is in the tree does not exist in the home or base directory then create it
            if base_folder_name not in home_folders_names:
                folder = Folder.objects.create(user=user, name=folder_name)
            else:
                # if exist then get it
                folder = Folder.objects.get(user=user, name=folder_name, parent_folder=None)
            # set current folder as a parent to the next folder
            parent_folder = folder
        else:
            # if the child folder not exist in parent children then create new one
            if folder_name not in parent_folder.folder_set.all().values_list('name', flat=True):
                folder = Folder.objects.create(user=user, name=folder_name, parent_folder=parent_folder)
            else:
                # get folder if exist
                folder = Folder.objects.get(user=user, name=folder_name, parent_folder=parent_folder)

            # set current folder as a parent to the next folder
            parent_folder = folder

    # return end of tree folder id
    return parent_folder


# Upload File API
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

        # sum all files sizes for checking user usage limit
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
                # check if directory id is valid integer number
                try:
                    directory_id = int(directory_id)
                except ValueError:
                    content['message'] = 'Directory ID must be an integer.'
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # get file upload destination
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

                except Exception as error:
                    content['message'] = str(error)
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)

                # this check is for returning directory id in the response
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
                # append file data to links list
                links.append(content)
        else:
            # this error if the user reached his usage limit
            content['message'] = 'Limit Exceeded!'
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    else:
        # this error message if the request body has no file object to upload
        content['message'] = 'No file to upload.'
        return Response(content, status=status.HTTP_404_NOT_FOUND)

    if len(links) > 1:
        # return uploaded files data
        return Response({"files": links})
    else:
        # return uploaded file data
        return Response({"file": links[0]})

# Delete file API ( it is not used yet! )
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


# Create folder tree API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_folder_tree(request, format=None):

    # get the current user
    user = request.user

    # get folder tree as a string
    folder_tree = request.POST['folder_tree']

    # get folder tree ID or create new one
    parent_folder = create_folder_tree_if_not_exist(folder_tree, user)

    content = {
    'message': 'Folders Created Successfully!',
    'directory_id': parent_folder.id
    }
    return Response(content)

# Delete Folder API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_folder(request, format=None):
    content = {}

    # get current user
    user = request.user
    # get folder tree data from the request
    folder_tree = request.POST['folder_tree']
    # split folder tree and convert it to a list of folders
    folder_tree = folder_tree.split('/')
    # is for cleaning folder tree from '' or None values
    folder_tree = list(filter(None, folder_tree))

    # get a list of all folders in base directory (Home)
    home_folders_names = Folder.objects.filter(user=user, parent_folder=None).values_list('name', flat=True)
    # get the fist folder in folder tree
    base_folder_name = folder_tree[0]

    # check if the first folder in the tree exist in the home or base directory
    if base_folder_name in home_folders_names:
        # if the first folder exist in home directory then get it
        parent_folder = Folder.objects.get(user=user, name=base_folder_name)
        # if folder tree is more than one folder then the user want to delete a child folder
        if len(folder_tree) > 1:

            folder = None
            # check every folder in the folder tree if it exists until arrive at the last one to delete it
            for index, folder_name in enumerate(folder_tree[1:]):
                try:
                    folder = Folder.objects.get(user=user, name=folder_name, parent_folder=parent_folder)
                    parent_folder = folder
                # if at least one folder in the folder tree does not exist then raise an exception error
                except Folder.DoesNotExist:
                    content['message'] = 'Folder does not exist.'
                    return Response(content)
            # if no exceptions then it means that all folders are exist
            # then delete this folder
            folder.delete()
            content['message'] = 'Folder Removed Successfully!'
            return Response(content)

        # if folder tree has only one folder, then delete this folder
        else:
            parent_folder.delete()
            content['message'] = 'Folder Removed Successfully!'
            return Response(content)

    # return an error message if the folder is not exist
    else:
        content['message'] = 'Folder does not exist.'


    return Response(content)

# this function is for getting file category
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
