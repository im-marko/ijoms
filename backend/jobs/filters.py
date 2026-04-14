from django_filters import rest_framework as filters
from .models import Job


class JobFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    sla_breached = filters.BooleanFilter(method='filter_sla_breached')

    class Meta:
        model = Job
        fields = ['status', 'priority', 'category', 'assigned_to', 'created_by']

    def filter_sla_breached(self, queryset, name, value):
        from django.utils import timezone
        now = timezone.now()
        if value:
            return queryset.filter(sla_deadline__lt=now).exclude(status='closed')
        return queryset.filter(sla_deadline__gte=now)
