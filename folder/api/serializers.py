from rest_framework import serializers
from folder.models import Folder

class FolderTreeSerializer(serializers.ModelSerializer):
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
        return FolderTreeSerializer(folder.get_folder_tree(), many=True, read_only=True).data
