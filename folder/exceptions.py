# Rest Framework
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound

# Project base
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

class FolderNotFoundError(NotFound):
    default_detail = (error_messages['not_found'])
    default_code = 'error'

class MoveFolderSameDestinationError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = (error_messages['move_to_same_destination'])
    default_code = 'error'
