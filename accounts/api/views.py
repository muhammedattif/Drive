from django.shortcuts import render
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound
from django.contrib.auth.decorators import permission_required
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework.authtoken.models import Token
from rest_framework import status
from folder.models import Folder
from file.models import File, SharedObject, SharedObjectPermission
from file.api.serializers import SharedObjectSerializer
import cloud.messages as response_messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from django.http import FileResponse, HttpResponse
import os
from folder.exceptions import (
FolderNewNameAlreadyExits,
RenameFolderRuntimeError,
UnknownError,
InBlockList
)
import cloud.messages as response_messages
from django.contrib.contenttypes.models import ContentType

User = get_user_model()


# class based view
class ObtainAuthTokenView(APIView):

	authentication_classes = []
	permission_classes = []

	def post(self, request):
		context = {}

		email = request.POST.get('email')
		password = request.POST.get('password')
		account = authenticate(email=email, password=password)
		if account:
			try:
				token = Token.objects.get(user=account)
			except Token.DoesNotExist:
				token = Token.objects.create(user=account)
			context['message'] = 'Successfully authenticated.'
			context['pk'] = account.pk
			context['email'] = email.lower()
			context['token'] = token.key
			return Response(context)
		else:
			context['message'] = 'Invalid credentials'
			return Response(context, status=status.HTTP_404_NOT_FOUND)


# Shared Files
class SharedListCreateView(APIView, PageNumberPagination):

	def get(self, request):

		blocked_users = request.user.file_sharing_block_list.users.values_list('id')
		shared_files = request.user.shared_files.prefetch_related('shared_by', 'shared_with', 'permissions', 'content_type', 'content_object').filter(
		~Q(shared_with__file_sharing_block_list__users__in=[request.user]),
		~Q(shared_by__in=blocked_users),
		~Q(shared_with__in=blocked_users)
		)

		shared_files = self.paginate_queryset(shared_files, request, view=self)
		serializer = SharedObjectSerializer(shared_files, many=True)
		return self.get_paginated_response(serializer.data)

	@transaction.atomic
	def post(self, request):
		required_fields = []
		if 'object_type' not in request.data:
			required_fields.append('object_type')
		if 'object_uuid' not in request.data:
			required_fields.append('object_uuid')
		if 'shared_with' not in request.data:
			required_fields.append('shared_with')
		if 'permissions' not in request.data:
			required_fields.append('permissions')

		if required_fields:
			return Response(response_messages.error('required_fields', required_fields=required_fields), status=status.HTTP_400_BAD_REQUEST)

		object_type = request.data['object_type']
		object_uuid = request.data['object_uuid']
		shared_with = request.data['shared_with']
		permissions = request.data['permissions']
		shared_with = User.objects.prefetch_related('file_sharing_block_list__users').filter(email=shared_with).first()
		if not shared_with:
			return Response(response_messages.error('user_not_found'), status=status.HTTP_404_NOT_FOUND)

		if not self.request.user.can_share_with(shared_with):
			return Response(response_messages.error('share_files_denied'), status=status.HTTP_403_FORBIDDEN)

		if object_type == 'file':
			object = File.objects.filter(user=request.user, unique_id=object_uuid).first()
		elif object_type == 'folder':
			object = Folder.objects.filter(user=request.user, unique_id=object_uuid).first()
		else:
			return Response(response_messages.error('shared_object_key_error'), status=status.HTTP_400_BAD_REQUEST)

		if not object:
			return Response(response_messages.error('file_not_found'), status=status.HTTP_404_NOT_FOUND)

		shared_file, created = SharedObject.objects.get_or_create(
		shared_by=request.user,
		content_type=ContentType.objects.get(model=object_type),
		object_id=object.id,
		shared_with=shared_with
		)

		# TODO: Include it in the manager

		if created:
			SharedObjectPermission.objects.create(file=shared_file, **permissions)

		serializer = SharedObjectSerializer(shared_file, many=False, read_only=True, context={'request': request })
		return Response(serializer.data)


class SharedUpdateDestroyView(APIView):

	def get(self, request, sharing_id):
		shared_file = SharedObject.objects.filter(id=sharing_id, shared_by=request.user).first()
		if not shared_file:
			return Response(response_messages.error('file_not_found'), status=status.HTTP_404_NOT_FOUND)
		serializer = SharedObjectSerializer(shared_file, many=False)
		return Response(serializer.data)

	def put(self, request, sharing_id):

		required_fields = []
		if 'shared_with' not in request.data:
			required_fields.append('shared_with')
		if 'permissions' not in request.data:
			required_fields.append('permissions')

		if required_fields:
			return Response(response_messages.error('required_fields', required_fields=required_fields), status=status.HTTP_400_BAD_REQUEST)

		shared_file = SharedObject.objects.filter(id=sharing_id, shared_by=request.user).first()
		if not shared_file:
			return Response(response_messages.error('file_not_shared_yet'), status=status.HTTP_404_NOT_FOUND)

		shared_file.permissions.can_view = request.data['permissions']['can_view']
		shared_file.permissions.can_rename = request.data['permissions']['can_rename']
		shared_file.permissions.can_download = request.data['permissions']['can_download']
		shared_file.permissions.can_delete = request.data['permissions']['can_delete']
		shared_file.permissions.save(update_fields=['can_view', 'can_rename', 'can_download', 'can_delete'])

		serializer = SharedObjectSerializer(shared_file, many=False, read_only=True)
		return Response(serializer.data)

	def delete(self, request, sharing_id):

		shared_file = SharedObject.objects.filter(id=sharing_id, shared_by=request.user).first()
		if not shared_file:
			return Response(response_messages.error('file_not_found'), status=status.HTTP_404_NOT_FOUND)
		shared_file.delete()
		return Response(response_messages.success('deleted_successfully'))

# Shared With Me Files

class SharedWithMeList(APIView, PageNumberPagination):

	def get(self, request):

		blocked_users = request.user.file_sharing_block_list.users.values_list('id')
		files_shared_with_me = request.user.shared_with_me.prefetch_related('shared_by', 'shared_with', 'permissions', 'content_type', 'content_object').filter(\
		~Q(shared_with__file_sharing_block_list__users__in=[request.user]),
		~Q(shared_by__in=blocked_users),
		~Q(shared_with__in=blocked_users),
		permissions__can_view=True,
		)

		files_shared_with_me = self.paginate_queryset(files_shared_with_me, request, view=self)
		serializer = SharedObjectSerializer(files_shared_with_me, many=True, context={'request': request})
		return self.get_paginated_response(serializer.data)

# Shared With Me Operations on files
class SharedWithMeDestroyView(APIView):

	def delete(self, request, sharing_id):
		shared_file = request.user.shared_with_me.filter(id=sharing_id)
		if not shared_file:
			raise NotFound()
		shared_file.delete()
		return Response(response_messages.success('deleted_successfully'))

class SharedWithMeDestroyOriginalView(APIView):

	def delete(self, request, sharing_id):
		shared_file = request.user.shared_with_me.filter(id=sharing_id, permissions__can_view=True, permissions__can_delete=True).first()
		if not shared_file:
			raise PermissionDenied()
		shared_file.content_object.delete()
		return Response(response_messages.success('deleted_successfully'))


# Rename original folder
class SharedWithMeEditOriginalView(APIView):

	def put(self, request, sharing_id):

		shared_file = request.user.shared_with_me.select_related(
		'content_type',
		'shared_by__file_sharing_block_list',
		'shared_with__file_sharing_block_list'
		).filter(id=sharing_id, permissions__can_view=True, permissions__can_rename=True).first()

		if not shared_file:
			raise PermissionDenied()

		if not shared_file.shared_by.can_share_with(request.user):
			raise InBlockList()

		if shared_file.content_type.model == 'folder':
			owner_has_edit_perm = shared_file.shared_by.has_perm('folder.can_rename_folder')
			if not owner_has_edit_perm:
				raise PermissionDenied()
			return self.rename_folder(request, shared_file)

	def rename_folder(self, request, shared_file):

		current_folder = shared_file.content_object
		user = shared_file.shared_by
		try:
			folder_new_name = request.data['folder_new_name']

			# delete folder dir from physical storage
			if current_folder.parent_folder:

				folder_old_path = os.path.join(
					settings.MEDIA_ROOT,
					settings.DRIVE_PATH,
					str(user.unique_id),
					current_folder.parent_folder.get_folder_tree_as_dirs(),
					current_folder.name)

				folder_new_path = os.path.join(
					settings.MEDIA_ROOT,
					settings.DRIVE_PATH,
					str(user.unique_id),
					current_folder.parent_folder.get_folder_tree_as_dirs(),
					folder_new_name)

			else:
				folder_old_path = os.path.join(
					settings.MEDIA_ROOT,
					settings.DRIVE_PATH,
					str(user.unique_id),
					current_folder.name)

				folder_new_path = os.path.join(
					settings.MEDIA_ROOT,
					settings.DRIVE_PATH,
					str(user.unique_id),
					folder_new_name)

			# Query the DB to check if there is a folder with the new name
			is_folder_exists_in_db = Folder.objects.filter(user=user, name=folder_new_name, parent_folder=current_folder.parent_folder).exists()

			if os.path.exists(folder_new_path) or is_folder_exists_in_db:
				raise FolderNewNameAlreadyExits()

			if os.path.exists(folder_old_path):

				# Rename folder on the physical disk
				try:
					os.rename(folder_old_path, folder_new_path)
				except:
					raise RenameFolderRuntimeError()

			try:
				# Rename folder in DB
				current_folder.name = folder_new_name
				current_folder.save(update_fields=['name'])
			except:
				os.rename(folder_new_path, folder_old_path)
				raise RenameFolderRuntimeError()

			return Response(response_messages.success('folder_renamed_successfully'))

		except Exception as e:
			raise UnknownError()

	def rename_file(self, request, file, user):
		pass

class SharedWithMeDownloadView(APIView):


	def get(self, request, sharing_id):

		shared_file = request.user.shared_with_me.select_related(
		'content_type',
		'shared_by__file_sharing_block_list',
		'shared_with__file_sharing_block_list'
		).filter(id=sharing_id, permissions__can_view=True, permissions__can_download=True).first()

		if not shared_file:
			raise PermissionDenied()

		if not shared_file.shared_by.can_share_with(request.user):
			raise InBlockList()

		if shared_file.content_type.model == 'folder':
			owner_has_edit_perm = shared_file.shared_by.has_perm('folder.can_download_folder')
			if not owner_has_edit_perm:
				raise PermissionDenied()
			return self.download_folder(request, shared_file)

		elif shared_file.content_type.model == 'file':
			owner_has_edit_perm = shared_file.shared_by.has_perm('file.can_download_file')
			if not owner_has_edit_perm:
				raise PermissionDenied()
			return self.download_file(request, shared_file)

	def download_folder(self, request, shared_file):

		folder = shared_file.content_object
		folder_tree = folder.get_folder_tree_as_dirs()
		user = shared_file.shared_by

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

	def download_file(self, request, shared_file):
		file = shared_file.content_object
		user = shared_file.shared_by
		response = FileResponse(file.file, as_attachment=True)
		response['Content-Disposition'] = f'attachment; filename="{file.name}"'
		return response
