import logging

from django.contrib.auth import get_user_model
from django.utils import timezone

from auditlog.mixins import log_action
from .models import Job, JobStatusHistory

logger = logging.getLogger(__name__)

ESCALATABLE_STATUSES = [Job.Status.OPEN, Job.Status.ASSIGNED, Job.Status.IN_PROGRESS]


def escalate_overdue_jobs():
    """Escalate every non-closed job past its SLA deadline.

    Notifications stay strictly within each job's company. Returns the list
    of escalated jobs. Runs as the system (changed_by=None).
    """
    User = get_user_model()
    overdue = list(
        Job.objects.filter(
            status__in=ESCALATABLE_STATUSES,
            sla_deadline__lt=timezone.now(),
        )
        .select_related('assigned_to', 'created_by', 'category', 'company')
    )

    # One query for every affected company's managers, grouped by company.
    company_ids = {job.company_id for job in overdue}
    managers_by_company = {}
    for manager in User.objects.filter(
        role__in=['operations_manager', 'supervisor'],
        is_active=True, company_id__in=company_ids,
    ):
        managers_by_company.setdefault(manager.company_id, []).append(manager)

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
            company=job.company,
        )

        from notifications.services import notify_job_escalated
        recipients = set(managers_by_company.get(job.company_id, []))
        if job.assigned_to:
            recipients.add(job.assigned_to)
        if job.created_by:
            recipients.add(job.created_by)
        notify_job_escalated(job, recipients)

        escalated.append(job)
        logger.info('Auto-escalated %s (deadline %s)', job.reference_number, job.sla_deadline)

    return escalated
