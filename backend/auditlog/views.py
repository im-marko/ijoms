from rest_framework import generics
from django_filters import rest_framework as filters

from accounts.permissions import IsManagerOrAbove
from ijoms.tenancy import CompanyScopedQuerysetMixin
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    user_id = filters.NumberFilter(field_name='user__id')

    class Meta:
        model = AuditLog
        fields = ['action', 'entity_type', 'user_id', 'start_date', 'end_date']


class AuditLogListView(CompanyScopedQuerysetMixin, generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsManagerOrAbove]
    queryset = AuditLog.objects.select_related('user').all()
    filterset_class = AuditLogFilter
    search_fields = ['entity_type', 'entity_id', 'user__email', 'user__first_name']
    ordering_fields = ['created_at', 'action']
