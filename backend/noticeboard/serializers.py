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

    def validate_target_roles(self, value):
        from django.contrib.auth import get_user_model
        valid_roles = set(get_user_model().Role.values)
        if not isinstance(value, list):
            raise serializers.ValidationError('target_roles must be a list of role names.')
        invalid = [r for r in value if r not in valid_roles]
        if invalid:
            raise serializers.ValidationError(f'Invalid roles: {", ".join(invalid)}')
        return value
