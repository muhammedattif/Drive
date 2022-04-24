from django.urls import path
from folder.api.views import (
create_folder_tree,
delete_folder,
FolderCopyView,
FolderMoveView,
FolderDestroyView,
FoldeCreateView
)

app_name = 'folder'

urlpatterns = [
    path('', FoldeCreateView.as_view(), name='create'),
    path('create_folder', create_folder_tree, name='create_folder'),
    path('delete_folder', delete_folder, name='delete_folder'),

    path('<str:uuid>/delete', FolderDestroyView.as_view(), name='delete'),
    path('<str:uuid>/copy', FolderCopyView.as_view(), name='copy'),
    path('<str:uuid>/move', FolderMoveView.as_view(), name='move')
]
