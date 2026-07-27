import logging

from django.contrib.auth import get_user_model
from django.utils import timezone

from auditlog.mixins import log_action
from .models import Job, JobStatusHistory

logger = logging.getLogger(__name__)

ESCALATABLE_STATUSES = [Job.Status.OPEN, Job.Status.ASSIGNED, Job.Status.IN_PROGRESS]


def escalate_overdue_jobs():
    """Escalate every non-closed job past its SLA deadline.

    Returns the list of escalated jobs. Runs as the system (changed_by=None).
    """
    User = get_user_model()
    overdue = (
        Job.objects.filter(
            status__in=ESCALATABLE_STATUSES,
            sla_deadline__lt=timezone.now(),
        )
        .select_related('assigned_to', 'created_by', 'category')
    )

    managers = list(
        User.objects.filter(
            role__in=['operations_manager', 'supervisor'], is_active=True,
        )
    )

    escalated = []
    for job in overdue:
        old_status = job.status
        job.status = Job.Status.ESCALATED
        job.save()

        JobStatusHistory.objects.create(
            job=job, from_status=old_status, to_status=Job.Status.ESCALATED,
            changed_by=None, notes='Auto-escalated: SLA deadline breached',
        )
        log_action(
            user=None, action='escalation', entity_type='Job',
            entity_id=job.pk,
            changes={'from': old_status, 'to': Job.Status.ESCALATED.value,
                     'reason': 'SLA deadline breached'},
        )

        from notifications.services import notify_job_escalated
        recipients = set(managers)
        if job.assigned_to:
            recipients.add(job.assigned_to)
        if job.created_by:
            recipients.add(job.created_by)
        notify_job_escalated(job, recipients)

        escalated.append(job)
        logger.info('Auto-escalated %s (deadline %s)', job.reference_number, job.sla_deadline)

    return escalated
