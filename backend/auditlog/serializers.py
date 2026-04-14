from rest_framework import serializers
from .models import AuditLog
from accounts.serializers import UserSerializer


class AuditLogSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'user_detail', 'action', 'entity_type',
            'entity_id', 'changes', 'ip_address', 'user_agent', 'created_at',
        ]
