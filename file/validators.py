# Django
from django.core.exceptions import ValidationError


def validation_message(key):
    return ValidationError(validation_mesages[key])

validation_mesages = {
    'not_file_owner': 'The user is not the owner of the file.',
    'in_block_list': 'Ops, you cannot share, it seems that you blocked or are blocked by the user you want to share with',
    'download_folder_permission_denied': 'You don\'t have download folder permission to assign it to shared folders.',
    'rename_folder_permission_denied': 'You don\'t have rename folder permission to assign it to shared folders.'
}
