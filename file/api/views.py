from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from file.models import File
from file.utils import get_file_cat
from folder.utils import check_sub_folders_limit, create_folder_tree_if_not_exist

# Upload File API
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload(request, format=None):
    content = {}
    links = []

    # if request has file
    if bool(request.FILES.get('file', False)):

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
        if user.drive_settings.is_allowed_to_upload_files(files_size):

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
                         uploader=user, file_name=file_name,
                         file_size=file_size, file_type=file_type,
                         file_category=file_category,
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
                    'uploader': file.uploader.email,
                    'file_name': file.file_name,
                    'file_id': file.pk,
                    'file_link': file.get_url(),
                    'file_size': file.file_size,
                    'file_type': file.file_type,
                    'file_category': file.file_category,
                    'uploaded_at': file.uploaded_at,
                    'directory_id': directory_id
                }
                # append file data to links list
                links.append(content)
        else:
            # this error if the user reached his usage limit
            content['error_description'] = 'Limit Exceeded!'
            return Response(content, status=status.HTTP_507_INSUFFICIENT_STORAGE)
    else:
        # this error message if the request body has no file object to upload
        content['error_description'] = 'No file to upload.'
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

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
        file = File.objects.get(unique_id=unique_id, uploader=user)
        file.delete()
        content['success_message'] = 'File Deleted Successfully!'
        return Response(content, status=status.HTTP_200_OK)
    except File.DoesNotExist:
        content['error_description'] = 'File Does not Exists!'
        return Response(content, status=status.HTTP_404_NOT_FOUND)
    except Exception as error:
        content['error_description'] = error
        return Response(content, status=status.HTTP_404_NOT_FOUND)

