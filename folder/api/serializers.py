# Rest Framework
from rest_framework import serializers

# Files app
from file.models import File

# Local Django
from folder.models import Folder


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class BasicFolderInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        exclude = ('user', )

class FolderSerializer(serializers.ModelSerializer):

    folder_tree = serializers.SerializerMethodField()
    sub_files_count = serializers.IntegerField()
    sub_folders_count = serializers.IntegerField()
    class Meta:
        model = Folder
        fields = '__all__'

    def get_folder_tree(self, folder):
        return BasicFolderInfoSerializer(folder.get_folder_tree(), many=True, read_only=True).data
