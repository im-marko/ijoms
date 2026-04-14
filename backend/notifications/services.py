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


def send_whatsapp_notification(recipient, message, related_job=None):
    notification = Notification.objects.create(
        recipient=recipient, type=Notification.Type.WHATSAPP,
        subject='WhatsApp Notification', message=message, related_job=related_job,
    )
    if not settings.WHATSAPP_PHONE_NUMBER_ID or not settings.WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp not configured, skipping.")
        notification.status = Notification.Status.FAILED
        notification.save()
        return notification

    if not recipient.phone:
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
        payload = {
            'messaging_product': 'whatsapp',
            'to': recipient.phone,
            'type': 'text',
            'text': {'body': message},
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=10)
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
