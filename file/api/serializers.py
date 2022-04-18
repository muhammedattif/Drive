from rest_framework import serializers
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.urls import reverse
import hashlib
from file.models import FileQuality
from django.conf import settings
from file.models import File, SharedObject, SharedObjectPermission
from drf_writable_nested.serializers import WritableNestedModelSerializer
from django.contrib.auth import get_user_model
from accounts.api.serializers import BasicUserInfoSerializer
from folder.api.serializers import FolderSerializer

class QualitySerializer(serializers.Serializer):
    quality = serializers.CharField()
    url = serializers.SerializerMethodField()

    def get_url(self, file):
        request = self.context.get('request')
        current_date = datetime.now() + relativedelta(minutes=+360)
        expiry = datetime.timestamp(current_date)
        plain_link = str(settings.ENCRYPTION_SECRET_KEY) + str(file.converted_file.unique_id) + str(expiry) + file.quality
        token = hashlib.md5(plain_link.encode('utf-8'))

        url = request.build_absolute_uri(reverse('file_api:stream', kwargs={
            'uuid': file.converted_file.unique_id,
            'token': token.hexdigest(),
            'expiry': expiry,
            'quality': file.quality
        }))
        return url

class OriginalQualitySerializer(serializers.Serializer):
    quality = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_quality(self, file):
        return file.properties.quality

    def get_url(self, file):
        request = self.context.get('request')
        current_date = datetime.now() + relativedelta(minutes=+360)
        expiry = datetime.timestamp(current_date)
        plain_link = str(settings.ENCRYPTION_SECRET_KEY) + str(file.unique_id) + str(expiry) + file.properties.quality
        token = hashlib.md5(plain_link.encode('utf-8'))

        url = request.build_absolute_uri(reverse('file_api:stream', kwargs={
            'uuid': file.unique_id,
            'token': token.hexdigest(),
            'expiry': expiry,
            'quality': file.properties.quality
        }))
        return url

class SubtitlesSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    def get_url(self, subtitle):
        request = self.context.get('request')
        subtitle_url = subtitle.subtitle_file.url
        return request.build_absolute_uri(subtitle_url)

    def get_language(self, obj):
        return obj.language

    def get_label(self, obj):
        return obj.get_language_display()

class CoverSerializer(serializers.Serializer):
    quality = serializers.CharField()
    cover_url = serializers.SerializerMethodField()

    def get_cover_url(self, props):
        request = self.context.get('request')
        if not props.cover:
            return ''
        cover_url = props.cover.url
        return request.build_absolute_uri(cover_url)

class FileQualitySerilizer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    class Meta:
        model = FileQuality
        fields = '__all__'

    def get_status(self, obj):
        return obj.get_status_display()

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'

class SharedObjectPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedObjectPermission
        fields = ('pk', 'can_view', 'can_rename', 'can_download', 'can_delete')


class SharedObjectSerializer(serializers.ModelSerializer):
    permissions = SharedObjectPermissionSerializer(many=False)
    shared_by = BasicUserInfoSerializer(many=False, read_only=True)
    shared_with = BasicUserInfoSerializer(many=False, read_only=True)
    content_object = serializers.SerializerMethodField()
    content_type = serializers.SerializerMethodField()

    class Meta:
        model = SharedObject
        fields = ('pk', 'content_object', 'content_type', 'shared_by', 'shared_with', 'permissions')

    def get_content_object(self, shared_object):
        if self.get_content_type(shared_object) == 'file':
            return FileSerializer(shared_object.content_object, many=False, read_only=True, context=self.context).data
        return FolderSerializer(shared_object.content_object, many=False, read_only=True).data

    def get_content_type(self, shared_object):
        return shared_object.content_type.model
