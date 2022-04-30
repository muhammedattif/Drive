from rest_framework.exceptions import APIException, NotFound
from rest_framework import status
from cloud.messages import error_messages

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
