# Rest Framework
from rest_framework import permissions


class CopyFilePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('file.can_copy_file')

class MoveFilePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.has_perm('file.can_move_file')
