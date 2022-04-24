from rest_framework import permissions

class CreateFolderPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('folder.can_create_folder')

class DownloadFolderPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('folder.can_download_folder')

class CopyFolderPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('folder.can_copy_folder')

class MoveFolderPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('folder.can_move_folder')
