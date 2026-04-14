from datetime import timedelta
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone

from jobs.models import Job, JobStatusHistory


def get_job_summary():
    """Counts of jobs by status and priority."""
    by_status = dict(
        Job.objects.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
    )
    by_priority = dict(
        Job.objects.values_list('priority').annotate(count=Count('id')).values_list('priority', 'count')
    )
    total = Job.objects.count()
    return {'total': total, 'by_status': by_status, 'by_priority': by_priority}


def get_sla_compliance():
    """Percentage of closed jobs that met SLA."""
    closed = Job.objects.filter(status='closed')
    total_closed = closed.count()
    if total_closed == 0:
        return {'total_closed': 0, 'met_sla': 0, 'breached_sla': 0, 'compliance_rate': 0}
    met = closed.filter(closed_at__lte=F('sla_deadline')).count()
    return {
        'total_closed': total_closed,
        'met_sla': met,
        'breached_sla': total_closed - met,
        'compliance_rate': round(met / total_closed * 100, 1),
    }


def get_technician_performance():
    """Jobs per technician with avg resolution time."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    technicians = User.objects.filter(role='technician', is_active=True)
    results = []
    for tech in technicians:
        assigned = Job.objects.filter(assigned_to=tech)
        closed = assigned.filter(status='closed', closed_at__isnull=False)
        total = assigned.count()
        completed = closed.count()
        # Avg resolution time in hours
        avg_hours = None
        if completed > 0:
            durations = []
            for job in closed:
                if job.closed_at and job.created_at:
                    durations.append((job.closed_at - job.created_at).total_seconds() / 3600)
            avg_hours = round(sum(durations) / len(durations), 1) if durations else None
        results.append({
            'technician_id': tech.id,
            'name': tech.get_full_name(),
            'total_jobs': total,
            'completed': completed,
            'in_progress': assigned.filter(status__in=['assigned', 'in_progress']).count(),
            'avg_resolution_hours': avg_hours,
        })
    return results


def get_job_volume_over_time(period='daily', days=30):
    """Job creation volume grouped by day/week/month."""
    since = timezone.now() - timedelta(days=days)
    qs = Job.objects.filter(created_at__gte=since)

    trunc_fn = {'daily': TruncDate, 'weekly': TruncWeek, 'monthly': TruncMonth}.get(period, TruncDate)
    data = (
        qs.annotate(period=trunc_fn('created_at'))
        .values('period')
        .annotate(count=Count('id'))
        .order_by('period')
    )
    return list(data)


def get_escalation_trends(days=90):
    """Escalation counts over time."""
    since = timezone.now() - timedelta(days=days)
    data = (
        JobStatusHistory.objects.filter(to_status='escalated', created_at__gte=since)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    return list(data)
