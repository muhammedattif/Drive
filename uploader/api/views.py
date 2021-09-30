from django.shortcuts import render
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from uploader.models import File, Folder
# Create your views here.

# Upload File
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request, format=None):
    content = {}
    links = []
    if bool(request.FILES.get('file', False)) == True:
        user = request.user
        for file in request.FILES.getlist('file'):
            uploaded_file = file
            file_name = uploaded_file.name
            file_size = uploaded_file.size
            file_category = get_file_cat(uploaded_file)
            file_type = uploaded_file.content_type
            file = File.objects.create(uploader=user, file_name=file_name, file_size=file_size, file_type=file_type, file_category=file_category, file=uploaded_file)
            content = {
                'uploader': file.uploader.email,
                'file_name': file.file_name,
                'file_id': file.pk,
                'file_link': file.get_url(),
                'file_size': file.file_size,
                'file_type': file.file_type,
                'file_category': file.file_category,
                'uploaded_at': file.uploaded_at
            }
            links.append(content)
    else:
        content['error'] = 'No file found'
        return Response(content)

    return Response(links)

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
def create_folder(request, format=None):

    user = request.user

    folder_tree = request.POST['folder_tree']
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

            if folder_name not in parent_folder.folder_set.all().values_list('name', flat=True):
                folder = Folder.objects.create(user=user, name=folder_name, parent_folder=parent_folder)
            else:
                folder = Folder.objects.get(user=user, name=folder_name, parent_folder=parent_folder)

            # set current folder as a parent to the next folder
            parent_folder = folder

    content = {'message': 'Folders Created Successfully!'}
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
