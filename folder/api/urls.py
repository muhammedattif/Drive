# Django
from django.urls import path

# Local Django
from folder.api.views import (FoldeCreateView, FolderCopyView,
                              FolderDestroyView, FolderDetailView,
                              FolderDownloadView, FolderFilesView,
                              FolderMoveView, FolderSubFoldersView,
                              create_folder_tree, delete_folder)

app_name = 'folder'

urlpatterns = [

    path('create_folder', create_folder_tree, name='create_folder'),
    path('delete_folder', delete_folder, name='delete_folder'),

    path('', FoldeCreateView.as_view(), name='create'),
    path('<str:uuid>/', FolderDetailView.as_view(), name='detail'),
    path('<str:uuid>/files', FolderFilesView.as_view(), name='folder-files'),
    path('<str:uuid>/folders', FolderSubFoldersView.as_view(), name='folder-subfiles'),
    path('<str:uuid>/delete', FolderDestroyView.as_view(), name='delete'),
    path('<str:uuid>/copy', FolderCopyView.as_view(), name='copy'),
    path('<str:uuid>/move', FolderMoveView.as_view(), name='move'),
    path('<str:uuid>/download', FolderDownloadView.as_view(), name='download'),
]
