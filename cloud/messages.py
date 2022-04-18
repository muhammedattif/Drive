
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
    'permission_denied': 'Permission Denied!'
}

success_messages = {
    'deleted_successfully': 'Deleted Successfully!',
    'folder_renamed_successfully': 'Folder Renamed Successfully!'
}
