# Django
from django.template.defaultfilters import filesizeformat

# Rest Framework
from rest_framework import serializers

# Drive App
from drive.models import DriveSettings, StoragePackage


class StoragePackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoragePackage
        fields = '__all__'

class DriveSettingsSerializer(serializers.ModelSerializer):
    storage_package = StoragePackageSerializer(many=False, read_only=True)
    storage_uploaded = serializers.SerializerMethodField()
    class Meta:
        model = DriveSettings
        fields = '__all__'

    def get_storage_uploaded(self, settings):
        return filesizeformat(settings.get_storage_uploaded_in_bytes())

class ClassifiedFileDataSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    size = serializers.SerializerMethodField()

    def get_size(self, type):
        return filesizeformat(type['size'])


class ClassifiedFilesSerializer(serializers.Serializer):
    images = ClassifiedFileDataSerializer(many=False, read_only=True)
    videos = ClassifiedFileDataSerializer(many=False, read_only=True)
    audio = ClassifiedFileDataSerializer(many=False, read_only=True)
    docs = ClassifiedFileDataSerializer(many=False, read_only=True)
    others = ClassifiedFileDataSerializer(many=False, read_only=True)
