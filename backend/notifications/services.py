import logging
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


def send_email_notification(recipient, subject, message, related_job=None):
    notification = Notification.objects.create(
        recipient=recipient, type=Notification.Type.EMAIL,
        subject=subject, message=message, related_job=related_job,
    )
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient.email])
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        notification.status = Notification.Status.FAILED
    notification.save()
    return notification


def _whatsapp_number(user):
    """Normalize a stored phone number to WhatsApp's E.164-without-plus format."""
    if not user.phone:
        return None
    digits = ''.join(ch for ch in user.phone if ch.isdigit())
    return digits or None


def _whatsapp_payload(to, message):
    """Template send when a template is configured (required for
    business-initiated messages outside the 24h service window),
    free-form text otherwise."""
    if settings.WHATSAPP_TEMPLATE_NAME:
        # Meta rejects template parameters containing newlines, tabs,
        # or runs of 4+ spaces — flatten the multi-line message.
        flat = ' | '.join(
            part.strip() for part in message.splitlines() if part.strip()
        )
        return {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'template',
            'template': {
                'name': settings.WHATSAPP_TEMPLATE_NAME,
                'language': {'code': settings.WHATSAPP_TEMPLATE_LANGUAGE},
                'components': [{
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': flat}],
                }],
            },
        }
    return {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': message},
    }


def send_whatsapp_notification(recipient, message, related_job=None, subject='WhatsApp Notification'):
    if not settings.WHATSAPP_ENABLED:
        return None

    notification = Notification.objects.create(
        recipient=recipient, type=Notification.Type.WHATSAPP,
        subject=subject, message=message, related_job=related_job,
    )
    to = _whatsapp_number(recipient)
    if not to:
        logger.warning(f"No phone number for {recipient.email}")
        notification.status = Notification.Status.FAILED
        notification.save()
        return notification

    try:
        url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
            'Content-Type': 'application/json',
        }
        resp = requests.post(url, json=_whatsapp_payload(to, message), headers=headers, timeout=10)
        resp.raise_for_status()
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        notification.status = Notification.Status.FAILED
    notification.save()
    return notification


def send_in_app_notification(recipient, subject, message, related_job=None):
    return Notification.objects.create(
        recipient=recipient, type=Notification.Type.IN_APP,
        subject=subject, message=message, related_job=related_job,
        status=Notification.Status.SENT, sent_at=timezone.now(),
    )


def notify_job_status_change(job, old_status, new_status, changed_by):
    """Send notifications on job status change."""
    subject = f"Job {job.reference_number} status: {old_status} → {new_status}"
    message = (
        f"Job: {job.title} ({job.reference_number})\n"
        f"Status changed from {old_status} to {new_status}\n"
        f"Changed by: {changed_by.get_full_name()}\n"
        f"Customer: {job.customer_name}"
    )

    recipients = set()
    if job.assigned_to and job.assigned_to != changed_by:
        recipients.add(job.assigned_to)
    if job.created_by and job.created_by != changed_by:
        recipients.add(job.created_by)

    for recipient in recipients:
        send_in_app_notification(recipient, subject, message, related_job=job)
        send_email_notification(recipient, subject, message, related_job=job)
        send_whatsapp_notification(recipient, message, related_job=job, subject=subject)


def notify_job_assigned(job, assigned_by):
    """Send notification when a job is assigned."""
    if not job.assigned_to:
        return
    subject = f"Job Assigned: {job.reference_number}"
    message = (
        f"You have been assigned job: {job.title} ({job.reference_number})\n"
        f"Priority: {job.get_priority_display()}\n"
        f"Customer: {job.customer_name}\n"
        f"Assigned by: {assigned_by.get_full_name()}"
    )
    send_in_app_notification(job.assigned_to, subject, message, related_job=job)
    send_email_notification(job.assigned_to, subject, message, related_job=job)
    send_whatsapp_notification(job.assigned_to, message, related_job=job, subject=subject)


def notify_job_escalated(job, recipients):
    """Send notifications when a job is auto-escalated for SLA breach."""
    subject = f"SLA BREACH — Job Escalated: {job.reference_number}"
    message = (
        f"Job: {job.title} ({job.reference_number})\n"
        f"Auto-escalated: SLA deadline breached\n"
        f"Deadline was: {job.sla_deadline:%Y-%m-%d %H:%M} UTC\n"
        f"Priority: {job.get_priority_display()}\n"
        f"Customer: {job.customer_name}\n"
        f"Assigned to: {job.assigned_to.get_full_name() if job.assigned_to else 'Unassigned'}"
    )
    for recipient in recipients:
        send_in_app_notification(recipient, subject, message, related_job=job)
        send_email_notification(recipient, subject, message, related_job=job)
        send_whatsapp_notification(recipient, message, related_job=job, subject=subject)
