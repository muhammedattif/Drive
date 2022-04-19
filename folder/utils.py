from folder.models import Folder
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
import shutil

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


import os
from shutil import *
def copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    print(names)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not os.path.isdir(dst): # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
                print(srcname)
            elif os.path.isdir(srcname):
                print(srcname)
                copytree(srcname, dstname, symlinks, ignore)
            else:
                print(srcname)
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentErrora as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)
