
def error(error_key):
    return {
        'status': False,
        'message': 'error',
        'error_description': error_messages[error_key]
    }

def success(success_key):
    return {
        'status': True,
        'message': 'success',
        'success_description': success_messages[success_key]
    }


error_messages = {
    'share_files_denied': 'You cannot share file with this user.',
    'user_not_found': 'User not found',
    'file_not_found': 'File Not Found!',
    'file_not_shared_yet': 'File is not shred with this user.',
}

success_messages = {
    'deleted_successfully': 'Deleted Successfully!'
}
