import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class JobCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    sla_hours = models.PositiveIntegerField(help_text='SLA deadline in hours')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Job categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Job(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        ASSIGNED = 'assigned', 'Assigned'
        IN_PROGRESS = 'in_progress', 'In Progress'
        ESCALATED = 'escalated', 'Escalated'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'

    VALID_TRANSITIONS = {
        Status.OPEN: [Status.ASSIGNED, Status.ESCALATED, Status.CLOSED],
        Status.ASSIGNED: [Status.IN_PROGRESS, Status.ESCALATED, Status.CLOSED],
        Status.IN_PROGRESS: [Status.ESCALATED, Status.CLOSED, Status.ASSIGNED],
        Status.ESCALATED: [Status.ASSIGNED, Status.IN_PROGRESS, Status.CLOSED],
        Status.CLOSED: [],
    }

    reference_number = models.CharField(max_length=20, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(JobCategory, on_delete=models.PROTECT, related_name='jobs')
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_jobs'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_jobs'
    )
    customer_name = models.CharField(max_length=200)
    customer_contact = models.CharField(max_length=50, blank=True)
    customer_email = models.EmailField(blank=True)
    sla_deadline = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['sla_deadline']),
        ]

    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"JOB-{uuid.uuid4().hex[:8].upper()}"
        if not self.sla_deadline and self.category_id:
            self.sla_deadline = timezone.now() + timezone.timedelta(hours=self.category.sla_hours)
        if self.status == self.Status.CLOSED and not self.closed_at:
            self.closed_at = timezone.now()
        super().save(*args, **kwargs)

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, [])

    def __str__(self):
        return f"{self.reference_number} - {self.title}"


class JobStatusHistory(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=15, choices=Job.Status.choices)
    to_status = models.CharField(max_length=15, choices=Job.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Job status histories'

    def __str__(self):
        return f"{self.job.reference_number}: {self.from_status} -> {self.to_status}"
