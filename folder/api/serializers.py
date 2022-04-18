from rest_framework import serializers
from folder.models import Folder

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        exclude = ('user', )
