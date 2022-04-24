from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.contrib.auth.decorators import permission_required
from django.contrib.auth import get_user_model
from django.db.models import Q, F
from file.models import File, FileQuality, SharedObject, SharedObjectPermission
from file.utils import get_file_cat
from folder.utils import check_sub_folders_limit, create_folder_tree_if_not_exist
from django.http import FileResponse, StreamingHttpResponse, HttpResponse
from rest_framework.views import APIView
import os
import re
from wsgiref.util import FileWrapper
from django.http.response import StreamingHttpResponse
from secrets import compare_digest
import hashlib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.urls import reverse
from file.utils import detect_quality
from .serializers import (
SubtitlesSerializer,
CoverSerializer,
QualitySerializer,
OriginalQualitySerializer,
EncrypredQualitySerializer,
EncrypredOriginalQualitySerializer,
FileQualitySerilizer,
SharedObjectSerializer
)
from django.conf import settings
from django.core.exceptions import ValidationError
import cloud.messages as response_messages

User = get_user_model()

# Upload File API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request, format=None):
    content = {}
    links = []

    # if request has file
    if not bool(request.FILES.get('file', False)):
        # this error message if the request body has no file object to upload
        content['error_description'] = 'No file to upload.'
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    uploaded_files = request.FILES.getlist('file')

    # get data from post request
    folder_tree = request.POST['folder_tree'] if 'folder_tree' in request.POST else None
    directory_id = request.POST['directory_id'] if 'directory_id' in request.POST else None
    privacy = request.POST['privacy'] if 'privacy' in request.POST else None

    files_size = 0

    # sum all files sizes for checking user usage limit
    for file in uploaded_files:
        files_size += file.size

    # check if the user is allowed to upload files with these size or his limit reached
    if not user.drive_settings.is_allowed_to_upload_files(files_size):
        # this error if the user reached his usage limit
        content['error_description'] = 'Limit Exceeded!'
        return Response(content, status=status.HTTP_507_INSUFFICIENT_STORAGE)

    parent_folder = None
    content = {}

    # if folder tree passed then get or create it
    if folder_tree:

        # Check sub folders limit
        limit_exceeded, response = check_sub_folders_limit(folder_tree)
        if limit_exceeded:
            return response

        parent_folder = create_folder_tree_if_not_exist(folder_tree, user)

    # if directory id passed then upload file to this directory
    elif directory_id:
        # check if directory id is valid integer number
        try:
            # get file upload destination
            parent_folder = Folder.objects.get(unique_id=directory_id, user=user)
        except Folder.DoesNotExist:
            content['message'] = 'Directory Not found.'
            return Response(content, status=status.HTTP_404_NOT_FOUND)

    # get all files in the request and upload it
    for file in uploaded_files:
        uploaded_file = file
        file_name = uploaded_file.name

        # Don't upload files that doesn't has extension
        if '.' not in file_name:
            content['error_description'] = 'Invalid File!'
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        file_size = uploaded_file.size
        file_category = get_file_cat(uploaded_file)
        file_type = uploaded_file.content_type
        try:
            file = File.objects.create(
                 user=user, name=file_name,
                 size=file_size, type=file_type,
                 category=file_category,
                 file=uploaded_file, parent_folder=parent_folder
            )
            # if privacy parameter passed then set it, if not then the default is 'private'
            if privacy:
                file.privacy.option = privacy
                file.privacy.save()

        except Exception as error:
            content['error_description'] = str(error)
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # this check is for returning directory id in the response
        if not parent_folder:
            directory_id = ''
        else:
            directory_id = parent_folder.unique_id

        content = {
            'user': file.user.email,
            'file_name': file.name,
            'file_id': file.pk,
            'file_link': file.get_url(),
            'file_size': file.size,
            'file_type': file.type,
            'file_category': file.category,
            'uploaded_at': file.uploaded_at,
            'directory_id': directory_id
        }
        # append file data to links list
        links.append(content)



    if len(links) > 1:
        # return uploaded files data
        return Response({"files": links})
    else:
        # return uploaded file data
        return Response({"file": links[0]})

# Delete file API ( it is not used yet! )
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete(request, unique_id):
    content = {}
    user = request.user
    try:
        file = File.objects.get(unique_id=unique_id, user=user)
        file.delete()
        content['success_message'] = 'File Deleted Successfully!'
        return Response(content, status=status.HTTP_200_OK)
    except File.DoesNotExist:
        content['error_description'] = 'File Does not Exists!'
        return Response(content, status=status.HTTP_404_NOT_FOUND)
    except Exception as error:
        content['error_description'] = error
        return Response(content, status=status.HTTP_404_NOT_FOUND)


class RangeFileWrapper(object):
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, 1)
        self.remaining = length
        self.blksize = length

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()

            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data

@api_view(['GET'])
@permission_classes([])
def stream_video(request, uuid, token, expiry, quality):

    if not check_url(request, uuid, token, expiry, quality):
        return Response({"error_description": 'Invalid URL'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        video = File.objects.get(unique_id=uuid).file
        path = video.path
    except File.DoesNotExist:
        return Response({"error_description": 'Video Does Not exists!'}, status=status.HTTP_400_BAD_REQUEST)


    range_header = request.META.get('HTTP_RANGE', '').strip()
    if not range_header:
        return Response({"error_description": 'Invalid Request'}, status=status.HTTP_400_BAD_REQUEST)

    range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    chunk_size = 1000000  # 1MB
    content_type = 'application/octet-stream'
    if range_match:

        start, end = range_match.groups()
        start = int(start)
        end = min(start + chunk_size, size - 1)
        length = (end - start) + 1

        resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'), offset=start, length=end), status=206, content_type=content_type)
        resp['Content-Length'] = length
        resp['Content-Range'] = 'bytes %s-%s/%s' % (start, end, size)
    else:
        return Response({"error_description": 'Invalid Request'}, status=status.HTTP_400_BAD_REQUEST)
    resp['Accept-Ranges'] = 'bytes'
    return resp


@api_view(['GET'])
@permission_classes([])
def generate_video_links(request, uuid):

    original_file_uuid = uuid

    try:
        original_file = File.objects.get(unique_id=original_file_uuid)
    except File.DoesNotExist:
        return Response({"error_description": 'Video Does Not exists!'}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError:
        return Response({"error_description": 'Invalid video UUID!'}, status=status.HTTP_400_BAD_REQUEST)

    file_qualities = original_file.qualities.filter(status='converted')
    subtitles = original_file.properties.subtitles.all()

    qualities_serializer = EncrypredQualitySerializer(file_qualities, many=True, context={'request': request})
    original_file_quality_serializer = EncrypredOriginalQualitySerializer(original_file, many=False, context={'request': request})

    subtitle_serializer = SubtitlesSerializer(subtitles, many=True, context={'request': request})
    properties_serializer = CoverSerializer(original_file.properties, many=False, context={'request': request})
    encrypted_urls = qualities_serializer.data
    encrypted_urls.append(original_file_quality_serializer.data)
    media_file_response = {
        'properties': properties_serializer.data,
        'subtitles': subtitle_serializer.data,
        'encrypted_urls': encrypted_urls
    }

    return Response(media_file_response)


@api_view(['GET'])
@permission_classes([])
def generate_video_links_for_iphone(request, uuid):

    original_file_uuid = uuid

    try:
        original_file = File.objects.get(unique_id=original_file_uuid)
    except File.DoesNotExist:
        return Response({"error_description": 'Video Does Not exists!'}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError:
        return Response({"error_description": 'Invalid video UUID!'}, status=status.HTTP_400_BAD_REQUEST)

    file_qualities = original_file.qualities.filter(status='converted')
    subtitles = original_file.properties.subtitles.all()

    qualities_serializer = QualitySerializer(file_qualities, many=True, context={'request': request})
    original_file_quality_serializer = OriginalQualitySerializer(original_file, many=False, context={'request': request})

    subtitle_serializer = SubtitlesSerializer(subtitles, many=True, context={'request': request})
    properties_serializer = CoverSerializer(original_file.properties, many=False, context={'request': request})

    encrypted_urls = qualities_serializer.data
    encrypted_urls.append(original_file_quality_serializer.data)
    media_file_response = {
        'properties': properties_serializer.data,
        'subtitles': subtitle_serializer.data,
        'encrypted_urls': encrypted_urls
    }

    return Response(media_file_response)


def check_url(request, uuid, token, expiry, quality):

    ip = get_user_ip_address(request)
    plain_link = str(settings.ENCRYPTION_SECRET_KEY) + str(uuid) + str(expiry) + quality
    generated_token = hashlib.md5(plain_link.encode('utf-8'))

    if not compare_digest(token, str(generated_token.hexdigest())):
        return False

    current_date = datetime.now()
    current_timestamp = datetime.timestamp(current_date)

    if current_timestamp > float(expiry):
        return False

    return True

def get_user_ip_address(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip



# Delete file API ( it is not used yet! )
@api_view(['GET'])
@permission_classes([])
def get_conversion_status(request, uuid):

    files = FileQuality.objects.filter(original_file__unique_id=uuid)
    serializer = FileQualitySerilizer(files, many=True)

    return Response(serializer.data)


class SharedWithListView(APIView):

    def get(self, request, uuid):

        file = File.objects.filter(user=request.user, unique_id=uuid).first()

        blocked_users = request.user.file_sharing_block_list.users.values_list('id')
        file_shared_with = SharedObject.objects.prefetch_related('shared_by', 'shared_with', 'permissions', 'content_type', 'content_object').filter(
        Q(shared_by=request.user),
        Q(object_id=file.id),
        ~Q(shared_with__file_sharing_block_list__users__in=[request.user]),
        ~Q(shared_by__in=blocked_users),
        ~Q(shared_with__in=blocked_users)
        )
        if not file:
            return Response(response_messages.error('file_not_found'), status=status.HTTP_404_NOT_FOUND)
        serializer = SharedObjectSerializer(file_shared_with, many=True, read_only=True, context={'request': request})
        return Response(serializer.data)
