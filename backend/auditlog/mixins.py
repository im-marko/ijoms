from .models import AuditLog
from .middleware import get_current_request


def log_action(user, action, entity_type, entity_id='', changes=None, request=None):
    if request is None:
        request = get_current_request()
    ip = ''
    user_agent = ''
    if request:
        ip = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        changes=changes or {},
        ip_address=ip or None,
        user_agent=user_agent,
    )


class AuditMixin:
    """Mixin for DRF views to auto-log create/update/delete."""
    audit_entity_type = ''

    def perform_create(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='create',
            entity_type=self.audit_entity_type or instance.__class__.__name__,
            entity_id=instance.pk,
            changes=serializer.validated_data,
            request=self.request,
        )
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(
            user=self.request.user,
            action='update',
            entity_type=self.audit_entity_type or instance.__class__.__name__,
            entity_id=instance.pk,
            changes=serializer.validated_data,
            request=self.request,
        )
        return instance

    def perform_destroy(self, instance):
        entity_id = instance.pk
        entity_type = self.audit_entity_type or instance.__class__.__name__
        instance.delete()
        log_action(
            user=self.request.user,
            action='delete',
            entity_type=entity_type,
            entity_id=entity_id,
            request=self.request,
        )
