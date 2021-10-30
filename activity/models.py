from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Activity(models.Model):
    UPLOAD_FILE = 'UPLOADFILE'
    TRASH_FILE = 'TRASHFILE'
    DELETE_FILE = 'DELETEFILE'
    CREATE_FOLDER = 'CREATEFOLDER'
    DELETE_FOLDER = 'DELETEFOLDER'
    RECOVER_FILE = 'RECOVERFILE'
    ACTIVITY_TYPES = (
        (UPLOAD_FILE, 'Upload File'),
        (TRASH_FILE, 'Trash File'),
        (DELETE_FILE, 'Delete File'),
        (RECOVER_FILE, 'Recover file'),
        (CREATE_FOLDER, 'Create Folder'),
        (DELETE_FOLDER, 'Delete Folder'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activities")
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    date = models.DateTimeField(auto_now_add=True)

    # Below the mandatory fields for generic relation
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    object_name = models.TextField(max_length=50)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        return f'{self.user.username}-{self.get_activity_type_display()}-{self.object_name}'
