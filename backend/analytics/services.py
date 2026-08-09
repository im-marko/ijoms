from datetime import timedelta
from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone

from jobs.models import Job, JobStatusHistory


def get_job_summary(assigned_to=None, company=None):
    """Counts of jobs by status and priority, scoped to a company and
    optionally one assignee."""
    qs = Job.objects.all()
    if company is not None:
        qs = qs.filter(company=company)
    if assigned_to is not None:
        qs = qs.filter(assigned_to=assigned_to)
    by_status = dict(
        qs.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
    )
    by_priority = dict(
        qs.values_list('priority').annotate(count=Count('id')).values_list('priority', 'count')
    )
    return {'total': qs.count(), 'by_status': by_status, 'by_priority': by_priority}


def get_sla_compliance(assigned_to=None, company=None):
    """Percentage of closed jobs that met SLA, plus open jobs currently past deadline."""
    base = Job.objects.all()
    if company is not None:
        base = base.filter(company=company)
    if assigned_to is not None:
        base = base.filter(assigned_to=assigned_to)
    open_breached = (
        base.exclude(status='closed')
        .filter(sla_deadline__lt=timezone.now())
        .count()
    )
    closed = base.filter(status='closed')
    total_closed = closed.count()
    if total_closed == 0:
        return {
            'total_closed': 0, 'met_sla': 0, 'breached_sla': 0,
            'compliance_rate': 0, 'open_breached': open_breached,
        }
    met = closed.filter(closed_at__lte=F('sla_deadline')).count()
    return {
        'total_closed': total_closed,
        'met_sla': met,
        'breached_sla': total_closed - met,
        'compliance_rate': round(met / total_closed * 100, 1),
        'open_breached': open_breached,
    }


def get_technician_performance(company=None):
    """Jobs per technician with avg resolution time."""
    from django.contrib.auth import get_user_model
    from django.db.models import DurationField, ExpressionWrapper
    User = get_user_model()
    closed_q = Q(assigned_jobs__status='closed', assigned_jobs__closed_at__isnull=False)
    tech_qs = User.objects.filter(role='technician', is_active=True)
    if company is not None:
        tech_qs = tech_qs.filter(company=company)
    technicians = (
        tech_qs
        .annotate(
            total_jobs=Count('assigned_jobs'),
            completed=Count('assigned_jobs', filter=closed_q),
            in_progress_count=Count(
                'assigned_jobs',
                filter=Q(assigned_jobs__status__in=['assigned', 'in_progress']),
            ),
            avg_resolution=Avg(
                ExpressionWrapper(
                    F('assigned_jobs__closed_at') - F('assigned_jobs__created_at'),
                    output_field=DurationField(),
                ),
                filter=closed_q,
            ),
        )
    )
    return [
        {
            'technician_id': tech.id,
            'name': tech.get_full_name(),
            'total_jobs': tech.total_jobs,
            'completed': tech.completed,
            'in_progress': tech.in_progress_count,
            'avg_resolution_hours': (
                round(tech.avg_resolution.total_seconds() / 3600, 1)
                if tech.avg_resolution else None
            ),
        }
        for tech in technicians
    ]


def get_job_volume_over_time(period='daily', days=30, company=None):
    """Job creation volume grouped by day/week/month."""
    since = timezone.now() - timedelta(days=days)
    qs = Job.objects.filter(created_at__gte=since)
    if company is not None:
        qs = qs.filter(company=company)

    trunc_fn = {'daily': TruncDate, 'weekly': TruncWeek, 'monthly': TruncMonth}.get(period, TruncDate)
    data = (
        qs.annotate(period=trunc_fn('created_at'))
        .values('period')
        .annotate(count=Count('id'))
        .order_by('period')
    )
    return list(data)


def get_escalation_trends(days=90, company=None):
    """Escalation counts over time."""
    since = timezone.now() - timedelta(days=days)
    qs = JobStatusHistory.objects.filter(to_status='escalated', created_at__gte=since)
    if company is not None:
        qs = qs.filter(job__company=company)
    data = (
        qs
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    return list(data)
