from rest_framework.exceptions import APIException
from rest_framework import status

class FolderNewNameAlreadyExits(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ('Folder with the new name is already exists.')
    default_code = 'error'

class RenameFolderRuntimeError(APIException):
    pass

class UnknownError(APIException):
    pass

class InBlockList(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = ('You are in the Blocklist or you have blocked this user.')
    default_code = 'error'