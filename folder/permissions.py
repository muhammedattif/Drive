from rest_framework import permissions

class CopyFolderPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('folder.can_copy_folder')

class MoveFolderPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('folder.can_move_folder')
