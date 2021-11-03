from folder.models import Folder
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status

def check_sub_folders_limit(folder_tree):
    if len(folder_tree.split('/')) > settings.SUB_FOLDERS_LIMIT:
        content = {
            'error_description': f'{folder_tree[-1]} cannot be created, sub folders limit is {settings.SUB_FOLDERS_LIMIT} !.'
        }
        return True, Response(content, status=status.HTTP_400_BAD_REQUEST)
    return False, None


# this function create folder tree if not exist and return directory object
def create_folder_tree_if_not_exist(folder_tree, user):

    parent_folder = None

    # split folder tree and convert it to a list of folders
    folder_tree = folder_tree.split('/')
    # remove none or empty values form the list
    folder_tree = list(filter(None, folder_tree))

    for index, folder_name in enumerate(folder_tree):
        # this check is because the home directory does not have a parent folder
        if index == 0:
            # in case the first folder is in the tree does not exist in the home or base directory then create it
            parent_folder, created = Folder.objects.get_or_create(user=user, name=folder_name, parent_folder=None)
        else:
            # in case the child folder not exist in parent children then create new one
            parent_folder, created = Folder.objects.get_or_create(user=user, name=folder_name,
                                                                  parent_folder=parent_folder)
    # return end of tree folder id
    return parent_folder