from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from file.models import File
from folder.models import Folder
from folder.utils import check_sub_folders_limit, create_folder_tree_if_not_exist
from django.conf import settings
from folder import utils
from folder.exceptions import UnknownError
from cloud import messages as response_messages
from folder.permissions import CopyFolderPermission, MoveFolderPermission
from folder.api.serializers import FolderSerializer

# Third-Party Libs
import os
import pathlib
import shutil

class FoldeCreateView(APIView):

    def post(self, request):

        if not ('folder_name' in request.data or request.data['folder_name']):
            return Response(response_messages.error('folder_name_empty'), status=status.HTTP_404_NOT_FOUND)
        folder_name = request.data['folder_name']

        if 'parent_folder_id' in request.data and request.data['parent_folder_id']:
            parent_folder_id = request.data['parent_folder_id']
            parent_folder = Folder.objects.filter(unique_id=parent_folder_id, user=request.user).first()
            if not parent_folder:
                return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

            if len(parent_folder.get_folder_tree()) > settings.SUB_FOLDERS_LIMIT:
                return Response(messages.error('sub_folders_limit_exceeded'), status=status.HTTP_400_BAD_REQUEST)

        else:
            parent_folder = None

        new_folder, created = Folder.objects.get_or_create(user=request.user, name=folder_name, parent_folder=parent_folder)
        if not created:
            return Response(response_messages.error('folder_exists'), status=status.HTTP_409_CONFLICT)

        serializer = FolderSerializer(new_folder, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# Deprecated
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

# Deprecated
# Delete Folder API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@permission_required('folder.delete_folder', raise_exception=True)
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


class FolderDestroyView(APIView):

    def delete(self, request, uuid):

        folder = Folder.objects.filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)
        folder.delete()
        return Response(response_messages.success('deleted_successfully'))



class FolderCopyView(APIView, CopyFolderPermission):

    permission_classes = [CopyFolderPermission]

    def put(self, request, uuid):

        destination_folder_id = request.data['destination_folder_id']

        folder = Folder.objects.filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

        folder_current_path = folder.get_path_on_disk()

        destination_folder = Folder.objects.filter(unique_id=destination_folder_id, user=request.user).first()
        if not destination_folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

        destination_path = destination_folder.get_path_on_disk()

        if self.is_destination_subfolder_of_source(folder_current_path, destination_path):
            raise UnknownError(detail='The destination folder is a subfolder of the source folder.')

        destination_path = os.path.join(destination_path, folder.name)

        if self.is_destination_equal_source(folder_current_path, destination_path):
            raise UnknownError(detail='The destination folder is same as the source folder.')

        try:
            self.copy_folder(folder_current_path, destination_path)
        except IOError as e:
            raise UnknownError(detail=e)
        return Response(response_messages.success('copied_successfully'))

    def copy_folder(self, folder_current_path, destination_path):
        from folder.utils import copytree
        copytree(
        folder_current_path,
        destination_path
        )

    def is_destination_equal_source(self, folder_current_path, destination_path):
        if folder_current_path == destination_path:
            return True
        return False

    def is_destination_subfolder_of_source(self, folder_current_path, destination_path):
        folder_current_path = pathlib.Path(folder_current_path)
        destination_path = pathlib.Path(destination_path)
        return destination_path.is_relative_to(folder_current_path)

class FolderMoveView(APIView):

    permission_classes = [MoveFolderPermission]

    def put(self, request, uuid):

        folder = Folder.objects.filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

        folder_current_path = folder.get_path_on_disk()

        if 'destination_folder_id' in request.data and request.data['destination_folder_id']:
            destination_folder_id = request.data['destination_folder_id']
            destination_folder = Folder.objects.prefetch_related('folder_set').filter(unique_id=destination_folder_id, user=request.user).first()
            if not destination_folder:
                return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

            destination_dir_folder_names = destination_folder.folder_set.values_list('name', flat=True)
            if folder.name in destination_dir_folder_names:
                return Response(response_messages.error('exists_in_destination'), status=status.HTTP_409_CONFLICT)

            destination_path = destination_folder.get_path_on_disk()
        else:
            destination_folder = None
            destination_path = os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(request.user.unique_id))
            base_dir_folder_names = Folder.objects.filter(user=request.user, parent_folder=None).values_list('name', flat=True)
            if folder.name in base_dir_folder_names:
                return Response(response_messages.error('exists_in_destination'), status=status.HTTP_409_CONFLICT)

        print(folder_current_path)
        print(destination_path)
        if self.is_destination_subfolder_of_source(folder_current_path, destination_path):
            raise UnknownError(detail='The destination folder is a subfolder of the source folder.')



        destination_path = os.path.join(destination_path, folder.name)
        if self.is_destination_equal_source(folder_current_path, destination_path):
            raise UnknownError(detail='The destination folder is same as the source folder.')

        try:
            self.move_folder(folder_current_path, destination_path)
        except IOError as e:
            raise UnknownError(detail=e)
        except OSError as e:
            raise UnknownError(detail=e)

        folder.parent_folder = destination_folder
        folder.save(update_fields=['parent_folder'])
        return Response(response_messages.success('moved_successfully'))

    def is_destination_equal_source(self, folder_current_path, destination_path):
        if folder_current_path == destination_path:
            return True
        return False

    def is_destination_subfolder_of_source(self, folder_current_path, destination_path):
        folder_current_path = pathlib.Path(folder_current_path)
        destination_path = pathlib.Path(destination_path)
        return destination_path.is_relative_to(folder_current_path)

    def is_copied_folder_exists_in_destination(copied_folder, destination_folder):
        pass

    def move_folder(self, folder_current_path, destination_path):
        shutil.move(
        folder_current_path,
        destination_path
        )
