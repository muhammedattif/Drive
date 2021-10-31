from folder.models import Folder

# this function create folder tree if not exist and return directory object
def create_folder_tree_if_not_exist(folder_tree, user):
    parent_folder = None

    # split folder tree and convert it to a list of folders
    folder_tree = folder_tree.split('/')
    # remove none or empty values form the list
    folder_tree = list(filter(None, folder_tree))

    for index, folder_name in enumerate(folder_tree):
        # this check is because the home directory does not have a parent folder
        if index == 0:
            # in case the first folder is in the tree does not exist in the home or base directory then create it
            parent_folder, created = Folder.objects.get_or_create(user=user, name=folder_name, parent_folder=None)
        else:
            # in case the child folder not exist in parent children then create new one
            parent_folder, created = Folder.objects.get_or_create(user=user, name=folder_name,
                                                                  parent_folder=parent_folder)

    # return end of tree folder id
    return parent_folder

def get_parent_folder(user, directory_id, folder_tree):

    parent_folder = None
    content = {}

    # if folder tree passed then get or create it
    if folder_tree:
        parent_folder = create_folder_tree_if_not_exist(folder_tree, user)

    # if directory id passed then upload file to this directory
    elif directory_id:
        # check if directory id is valid integer number
        try:
            # get file upload destination
            parent_folder = Folder.objects.get(unique_id=directory_id, user=user)
        except Folder.DoesNotExist:
            content['message'] = 'Directory Not found.'
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    return parent_folder
