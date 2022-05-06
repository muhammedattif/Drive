# Django
from django.urls import path

# Accounts App
from accounts.api.views import (ObtainAuthTokenView, SharedListCreateView,
                                SharedUpdateDestroyView,
                                SharedWithMeDestroyOriginalView,
                                SharedWithMeDestroyView,
                                SharedWithMeDownloadView,
                                SharedWithMeEditOriginalView, SharedWithMeList)

app_name = 'accounts'

urlpatterns = [
    path('login', ObtainAuthTokenView.as_view(), name="login"),

    # Shared Files
    path('shared-files', SharedListCreateView.as_view(), name="shared-objects"),
    path('shared-files/<int:sharing_id>/', SharedUpdateDestroyView.as_view(), name='delete-update-shared'),

    # Shared With Me Files
    path('shared-with-me', SharedWithMeList.as_view(), name="shared-with-me"),

    path('shared-with-me/<int:sharing_id>/remove', SharedWithMeDestroyView.as_view(), name="remove-shared-with-me"),

    path('shared-with-me/<int:sharing_id>/delete', SharedWithMeDestroyOriginalView.as_view(), name="delete-original-shared-file"),
    path('shared-with-me/<int:sharing_id>/edit', SharedWithMeEditOriginalView.as_view(), name="edit-original-shared-file"),
    path('shared-with-me/<int:sharing_id>/download', SharedWithMeDownloadView.as_view(), name="download-original-shared-file"),
  ]
