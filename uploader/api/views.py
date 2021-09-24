from django.shortcuts import render
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from uploader.models import File
# Create your views here.

# Upload File
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request, format=None):
    content = {}
    if bool(request.FILES.get('file', False)) == True:
        user = request.user

        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        file_category = get_file_cat(uploaded_file)
        file_type = uploaded_file.content_type
        file = File.objects.create(uploader=user, file_name=file_name, file_size=file_size, file_type=file_type, file_category=file_category, file=uploaded_file)
        content = {
            'uploader': file.uploader.email,
            'file_name': file.file_name,
            'file_id': file.pk,
            'file_link': file.get_url(),
            'file_size': file.file_size,
            'file_type': file.file_type,
            'file_category': file.file_category,
            'uploaded_at': file.uploaded_at
        }
    else:
        content['error'] = 'No file found'
    return Response(content)

# Delete File
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete(request, id):
    content = {}
    user = request.user
    try:
        file = File.objects.get(pk=id, uploader=user)
        file.delete()
        content['message'] = 'File Deleted Successfully!'
    except File.DoesNotExist:
        content['message'] = 'File Does not Exists!'
    return Response(content)


def get_file_cat(file):
    docs_ext =  ['pdf','doc','docx','xls','ppt','txt']
    if file.content_type.split('/')[0] == 'image':
        return 'images'
    elif file.content_type.split('/')[0] == 'audio' or file.content_type.split('/')[0] == 'video':
        return 'media'
    elif file.name.split('.')[-1] in docs_ext or file.content_type.split('/')[0] == 'text':
        return 'docs'
    else:
        return 'other'
