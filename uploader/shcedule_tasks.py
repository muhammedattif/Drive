from uploader.models import Trash
def delete_trashed_files():
    all_trashed_files = Trash.objects.all()
    for file in all_trashed_files:
        pass
