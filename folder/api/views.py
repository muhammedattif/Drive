# Standard library
import os

# Third-party
import pathlib
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

# Django
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.db import transaction
from django.http import FileResponse

# Rest Framework
from rest_framework import status
from rest_framework.decorators import (api_view,
                                       permission_classes)
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Project base
from cloud import messages as response_messages
from cloud.exceptions import InsufficientStorageError, UnknownError

# Files App
from file.api.serializers import FileSerializer
from file.models import File, FilePrivacy, MediaFileProperties
from file.utils import detect_quality, generate_file_link

# Local Django
from folder.api.serializers import BasicFolderInfoSerializer, FolderSerializer
from folder.exceptions import (CopiedFolderAlreadyExits, FolderNotFoundError,
                               MoveFolderSameDestinationError)
from folder.models import Folder
from folder.permissions import (CopyFolderPermission, CreateFolderPermission,
                                DownloadFolderPermission, MoveFolderPermission)
from folder.utils import (check_sub_folders_limit,
                          create_folder_tree_if_not_exist)


class FoldeCreateView(APIView):

    permission_classes = [CreateFolderPermission]
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

class FolderDetailView(APIView):

    def get(self, request, uuid):

        folder = Folder.objects.select_related('parent_folder').annotate_sub_files_count().annotate_sub_folders_count().filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

        serializer = FolderSerializer(folder, many=False, read_only=True)
        return Response(serializer.data)

class FolderFilesView(APIView, PageNumberPagination):

    def get(self, request, uuid):

        folder = Folder.objects.select_related('parent_folder').prefetch_related('files').filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

        files = folder.files.all()
        files = self.paginate_queryset(files, request, view=self)
        serializer = FileSerializer(files, many=True, read_only=True)
        return self.get_paginated_response(serializer.data)


class FolderSubFoldersView(APIView, PageNumberPagination):

    def get(self, request, uuid):

        folder = Folder.objects.select_related('parent_folder').prefetch_related('files').filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)

        files = folder.sub_folders.all()
        files = self.paginate_queryset(files, request, view=self)
        serializer = BasicFolderInfoSerializer(files, many=True, read_only=True)
        return self.get_paginated_response(serializer.data)

class FolderDownloadView(APIView):

    permission_classes = [DownloadFolderPermission]

    def get(self, request, uuid):

        folder = Folder.objects.get(user=request.user, unique_id=uuid)
        folder_tree = folder.get_folder_tree_as_dirs()

        user = request.user
        folder_to_compress = Path(os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(user.unique_id), folder_tree))

        path_to_archive_in_os = Path(
            os.path.join(settings.MEDIA_ROOT, settings.COMPRESS_PATH, f"{str(folder.name)}{'.zip'}"))

        with ZipFile(
                path_to_archive_in_os,
                mode="w",
                compression=ZIP_DEFLATED
        ) as zip:
            for file in folder_to_compress.rglob("*"):
                relative_path = file.relative_to(folder_to_compress)
                print(f"Packing {file} as {relative_path}")
                zip.write(file, arcname=relative_path)

        response = FileResponse(open(path_to_archive_in_os, 'rb'), as_attachment=True)
        response['Content-Disposition'] = 'attachment; filename={}'.format(folder.name + '.zip')
        return response

class FolderDestroyView(APIView):

    def delete(self, request, uuid):

        folder = Folder.objects.filter(unique_id=uuid, user=request.user).first()
        if not folder:
            return Response(response_messages.error('not_found'), status=status.HTTP_404_NOT_FOUND)
        folder.delete()
        return Response(response_messages.success('deleted_successfully'))



class FolderCopyView(APIView, CopyFolderPermission):

    permission_classes = [CopyFolderPermission]

    @transaction.atomic
    def put(self, request, uuid):

        folder = Folder.objects.prefetch_related('sub_folders', 'files').select_related('user').filter(unique_id=uuid, user=request.user).first()
        if not folder:
            raise FolderNotFoundError()

        folder_current_path = folder.get_path_on_disk()

        if 'destination_folder_id' in request.data and request.data['destination_folder_id']:
            destination_folder_id = request.data['destination_folder_id']
            destination_folder = Folder.objects.prefetch_related('sub_folders').filter(unique_id=destination_folder_id, user=request.user).first()
            if not destination_folder:
                raise FolderNotFoundError()

            destination_path = destination_folder.get_path_on_disk()
        else:
            destination_folder = None
            destination_path = os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(request.user.unique_id))

        try:
            folder_name = self.copy_folder_on_disk(folder_current_path, destination_path)
        except IOError as e:
            raise UnknownError(detail=e)

        new_folder = Folder.objects.create(name=folder_name, parent_folder=destination_folder, user=folder.user)


        objects_lists = {
        'files_objs': [],
        'privacy_objs': [],
        'media_props_objs': []
        }

        default_upload_privacy = request.user.drive_settings.default_upload_privacy
        created_objects, copied_files_size = self.copy_folder_db_relations(
                                                        folder,
                                                        new_folder,
                                                        default_upload_privacy,
                                                        objects_lists=objects_lists,
                                                        copied_files_size=0
                                                        )
        # Check if the user is allowed to copy files with these size or his limit reached
        if not request.user.drive_settings.is_allowed_to_upload_files(copied_files_size):
            raise InsufficientStorageError()
        # Update the drive settings for the user
        request.user.drive_settings.add_storage_uploaded(copied_files_size)
        request.user.drive_settings.save()

        # Create all the files and its properties
        files_objs = created_objects['files_objs']
        File.objects.bulk_create(files_objs)

        privacy_objs = created_objects['privacy_objs']
        FilePrivacy.objects.bulk_create(privacy_objs)

        media_props_objs = created_objects['media_props_objs']
        MediaFileProperties.objects.bulk_create(media_props_objs)


        return Response(response_messages.success('copied_successfully'))

    def copy_folder_db_relations(self, old_folder, new_folder, default_upload_privacy, objects_lists, copied_files_size):

        sub_files = old_folder.files.prefetch_related('parent_folder', 'user').all()
        for file in sub_files:

            new_file, new_file_privacy, media_file_props = self.deuplicate_file(
            old_file=file,
            parent_folder=new_folder,
            default_upload_privacy=default_upload_privacy
            )
            copied_files_size += new_file.size

            objects_lists['files_objs'].append(new_file)
            objects_lists['privacy_objs'].append(new_file_privacy)
            if media_file_props:
                objects_lists['media_props_objs'].append(media_file_props)



        sub_folders = old_folder.sub_folders.prefetch_related('sub_folders', 'files').select_related('user').all()
        for folder in sub_folders:
            new_child_folder = self.duplicate_folder(old_folder=folder, parent_folder=new_folder)
            # This Line HITS the Database
            new_child_folder.save()

            objects_lists, copied_files_size = self.copy_folder_db_relations(
            old_folder=folder,
            new_folder=new_child_folder,
            default_upload_privacy=default_upload_privacy,
            objects_lists=objects_lists,
            copied_files_size=copied_files_size
            )

        return objects_lists, copied_files_size

    def deuplicate_file(self, old_file, parent_folder, default_upload_privacy):

        if old_file.parent_folder:
            parent_folder_path = parent_folder.get_folder_tree_as_dirs()
            base_dir = f'{settings.DRIVE_PATH}/{str(old_file.user.unique_id)}'
            new_path = f'{base_dir}/{parent_folder_path}/{old_file.name}'
        else:
            base_dir = f'{settings.DRIVE_PATH}/{str(old_file.user.unique_id)}'
            new_path = f'{base_dir}/{old_file.name}'


        new_file = File(
        user=old_file.user,
        name=old_file.name,
        size=old_file.size,
        type=old_file.type,
        category=old_file.category,
        file=old_file.file,
        parent_folder=parent_folder
        )
        new_file.file.name = new_path

        new_file_privacy = FilePrivacy(file=new_file)
        new_file_privacy.option = default_upload_privacy
        new_file_privacy.link = generate_file_link(new_file.name)


        if new_file.category == 'media':
            media_file_quality = detect_quality(new_file.file.path)
            media_file_props = MediaFileProperties(media_file=new_file, quality=media_file_quality)
        else:
            return new_file, new_file_privacy, None

        return new_file, new_file_privacy, media_file_props

    def duplicate_folder(self, old_folder, parent_folder):
        new_folder = Folder(
        name=old_folder.name,
        parent_folder=parent_folder,
        user=old_folder.user
        )
        return new_folder


    def copy_folder_on_disk(self, folder_current_path, destination_path):
        from folder.utils import copytree # isort:skip

        if not Path(destination_path).is_dir():
            os.makedirs(destination_path)

        folder_name = os.path.basename(folder_current_path)
        old_destination_path = os.path.join(destination_path, folder_name)

        if Path(old_destination_path).is_dir():
            i = 1
            while os.path.exists(os.path.join(destination_path, folder_name + " " + str(i))):
                i+=1
            folder_name = folder_name + " " + str(i)

        new_destination_path = os.path.join(destination_path, folder_name)

        copytree(
        folder_current_path,
        new_destination_path
        )
        return folder_name

class FolderMoveView(APIView):

    permission_classes = [MoveFolderPermission]

    @transaction.atomic
    def put(self, request, uuid):

        folder = Folder.objects.filter(unique_id=uuid, user=request.user).first()
        if not folder:
            raise FolderNotFoundError()

        folder_current_path = folder.get_path_on_disk()

        if 'destination_folder_id' in request.data and request.data['destination_folder_id']:
            destination_folder_id = request.data['destination_folder_id']
            destination_folder = Folder.objects.prefetch_related('sub_folders').filter(unique_id=destination_folder_id, user=request.user).first()
            if not destination_folder:
                raise FolderNotFoundError()

            destination_path = destination_folder.get_path_on_disk()
        else:
            destination_folder = None
            destination_path = os.path.join(settings.MEDIA_ROOT, settings.DRIVE_PATH, str(request.user.unique_id))

        if folder.parent_folder == destination_folder:
            raise MoveFolderSameDestinationError()

        if self.is_destination_subfolder_of_source(folder_current_path, destination_path):
            raise UnknownError(detail='The destination folder is a subfolder of the source folder.')

        try:
            folder_name = self.move_folder(folder_current_path, destination_path)
        except IOError as e:
            raise UnknownError(detail=e)
        except OSError as e:
            raise UnknownError(detail=e)

        folder.parent_folder = destination_folder
        folder.name = folder_name
        folder.save(update_fields=['parent_folder', 'name'])
        return Response(response_messages.success('moved_successfully'))


    def is_destination_subfolder_of_source(self, folder_current_path, destination_path):
        folder_current_path = pathlib.Path(folder_current_path)
        destination_path = pathlib.Path(destination_path)
        return destination_path.is_relative_to(folder_current_path)


    def move_folder(self, folder_current_path, destination_path):
        if not Path(destination_path).is_dir():
            os.makedirs(destination_path)

        folder_name = os.path.basename(folder_current_path)
        old_destination_path = os.path.join(destination_path, folder_name)

        if Path(old_destination_path).is_dir():
            i = 1
            while os.path.exists(os.path.join(destination_path, folder_name + " " + str(i))):
                i+=1
            folder_name = folder_name + " " + str(i)

        new_destination_path = os.path.join(destination_path, folder_name)

        shutil.move(
        folder_current_path,
        new_destination_path
        )
        return folder_name




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
