from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Notice


class NoticeSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)

    class Meta:
        model = Notice
        fields = [
            'id', 'title', 'content', 'priority', 'target_roles',
            'expiry_date', 'is_active', 'created_by', 'created_by_detail',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_by']
