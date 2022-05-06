# Django
from django.contrib.auth import get_user_model

# Rest Framework
from rest_framework import serializers

User = get_user_model()

class BasicUserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
