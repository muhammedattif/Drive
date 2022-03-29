from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from file.models import File
from folder.models import Folder
from folder.utils import check_sub_folders_limit, create_folder_tree_if_not_exist

# Create folder tree API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_folder_tree(request, format=None):

    # get folder tree as a string
    folder_tree = request.POST['folder_tree']

    # Check sub folders limit
    limit_exceeded, response = check_sub_folders_limit(folder_tree)
    if limit_exceeded:
        return response

    # get the current user
    user = request.user

    # get folder tree ID or create new one
    parent_folder = create_folder_tree_if_not_exist(folder_tree, user)

    content = {
        'message': 'Folders Created Successfully!',
        'directory_id': parent_folder.unique_id
    }
    return Response(content, status=status.HTTP_201_CREATED)


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
    if base_folder_name not in home_folders_names:
        # return an error message if the folder is not exist
        content['message'] = 'Folder does not exist.'
        return Response(content, status=status.HTTP_404_NOT_FOUND)

    # if the first folder exist in home directory then get it
    parent_folder = Folder.objects.get(user=user, name=base_folder_name)
    # if folder tree is more than one folder then the user want to delete a child folder

    # TODO: we can enhance this code by getting the last folder in the tree and the compare its tree with the desired tree

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
                return Response(content, status=status.HTTP_404_NOT_FOUND)
        # if no exceptions then it means that all folders are exist
        # then delete this folder
        folder.delete()
        content['message'] = 'Folder Removed Successfully!'
        return Response(content, status=status.HTTP_200_OK)

    # if folder tree has only one folder, then delete this folder
    else:
        parent_folder.delete()
        content['message'] = 'Folder Removed Successfully!'
        return Response(content, status=status.HTTP_200_OK)
