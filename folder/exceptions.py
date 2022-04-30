from rest_framework.exceptions import APIException, NotFound
from rest_framework import status
from cloud.messages import error_messages

class FolderNewNameAlreadyExits(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = ('Folder with the new name is already exists.')
    default_code = 'error'

class CopiedFolderAlreadyExits(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (error_messages['exists_in_destination'])
    default_code = 'error'


class RenameFolderRuntimeError(APIException):
    pass

class UnknownError(APIException):
    pass

class InsufficientStorageError(APIException):
    status_code = status.HTTP_507_INSUFFICIENT_STORAGE
    default_detail = ('Storage Limit Exceeded!')
    default_code = 'error'

class InBlockList(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = ('You are in the Blocklist or you have blocked this user.')
    default_code = 'error'

class FolderNotFoundError(NotFound):
    default_detail = (error_messages['not_found'])
    default_code = 'error'

class MoveFolderSameDestinationError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (error_messages['move_to_same_destination'])
    default_code = 'error'
