from django.utils import timezone
from rest_framework import generics

from accounts.permissions import IsSupervisorOrAbove
from auditlog.mixins import AuditMixin
from .models import Notice
from .serializers import NoticeSerializer


class NoticeListView(generics.ListAPIView):
    serializer_class = NoticeSerializer

    def get_queryset(self):
        now = timezone.now()
        user_role = self.request.user.role
        qs = Notice.objects.filter(is_active=True).select_related('created_by')
        qs = qs.exclude(expiry_date__lt=now)
        # Filter in Python: notices targeting this role or all roles (empty list)
        matching_ids = [
            n.pk for n in qs
            if not n.target_roles or user_role in n.target_roles
        ]
        return qs.filter(pk__in=matching_ids)


class NoticeCreateView(AuditMixin, generics.CreateAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsSupervisorOrAbove]
    audit_entity_type = 'Notice'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class NoticeDetailView(AuditMixin, generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NoticeSerializer
    permission_classes = [IsSupervisorOrAbove]
    queryset = Notice.objects.all()
    audit_entity_type = 'Notice'
