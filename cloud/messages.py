from django.conf import settings

def error(error_key, **extra_data):
    return {
        'status': False,
        'message': 'error',
        'error_description': error_messages[error_key],
        **extra_data
    }

def success(success_key, **extra_data):
    return {
        'status': True,
        'message': 'success',
        'success_description': success_messages[success_key],
        **extra_data
    }


error_messages = {
    'share_files_denied': 'You cannot share file with this user.',
    'user_not_found': 'User not found',
    'file_not_found': 'File Not Found!',
    'file_not_shared_yet': 'File is not shred with this user.',
    'required_fields': 'Some fields are required.',
    'permission_denied': 'Permission Denied!',
    'not_found': 'Not Found!',
    'exists_in_destination': 'A folder with the name of the copied one already exists in this folder.',
    'folder_exists': 'A folder with the same name already exists.',
    'sub_folders_limit_exceeded': f'Sub folders limit is {settings.SUB_FOLDERS_LIMIT}!.',
    'folder_name_empty': "Ops, you forget to enter folder's name.",
    'move_to_same_destination': "Canot move Files/Folders to the same destination.",
    'shared_object_key_error': 'Object type must be one of the following (file, folder).'
}

success_messages = {
    'deleted_successfully': 'Deleted Successfully!',
    'folder_renamed_successfully': 'Folder Renamed Successfully!',
    'copied_successfully': 'Copied Successfully!',
    'moved_successfully': 'Moved Successfully!',
}
