from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CanViewJobs, CanManageJobs, IsSupervisorOrAbove
from auditlog.mixins import AuditMixin, log_action
from ijoms.tenancy import CompanyScopedQuerysetMixin
from .models import Job, JobCategory, JobStatusHistory
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateSerializer,
    JobUpdateSerializer, JobCategorySerializer, JobStatusUpdateSerializer,
    JobAssignSerializer,
)
from .filters import JobFilter

User = get_user_model()


class JobCategoryListCreateView(CompanyScopedQuerysetMixin, AuditMixin, generics.ListCreateAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    audit_entity_type = 'JobCategory'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [CanViewJobs()]
        return [IsSupervisorOrAbove()]

    def perform_create(self, serializer):
        instance = serializer.save(company=self.request.user.company)
        log_action(
            user=self.request.user, action='create', entity_type='JobCategory',
            entity_id=instance.pk, changes=serializer.validated_data,
            request=self.request,
        )
        return instance


class JobListView(CompanyScopedQuerysetMixin, generics.ListAPIView):
    serializer_class = JobListSerializer
    permission_classes = [CanViewJobs]
    filterset_class = JobFilter
    search_fields = ['title', 'reference_number', 'customer_name', 'description']
    ordering_fields = ['created_at', 'priority', 'status', 'sla_deadline']
    queryset = Job.objects.select_related('category', 'assigned_to', 'created_by')

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'technician':
            qs = qs.filter(assigned_to=self.request.user)
        return qs


class JobCreateView(AuditMixin, generics.CreateAPIView):
    serializer_class = JobCreateSerializer
    permission_classes = [CanManageJobs]
    audit_entity_type = 'Job'


class JobDetailView(CompanyScopedQuerysetMixin, AuditMixin, generics.RetrieveUpdateAPIView):
    serializer_class = JobDetailSerializer
    audit_entity_type = 'Job'
    queryset = Job.objects.select_related('category', 'assigned_to', 'created_by').prefetch_related('status_history')

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH'):
            return [CanManageJobs()]
        return [CanViewJobs()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return JobUpdateSerializer
        return JobDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role == 'technician':
            qs = qs.filter(assigned_to=self.request.user)
        return qs

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        response.data = JobDetailSerializer(instance, context={'request': request}).data
        return response


class JobStatusUpdateView(APIView):
    permission_classes = [CanViewJobs]

    def post(self, request, pk):
        try:
            job = Job.objects.filter(company_id=request.user.company_id).get(pk=pk)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Technicians can only update their own jobs
        if request.user.role == 'technician' and job.assigned_to != request.user:
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = JobStatusUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        if not job.can_transition_to(new_status):
            return Response(
                {'detail': f'Cannot transition from {job.status} to {new_status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Reopening a closed job is supervisor-and-above only
        if job.status == Job.Status.CLOSED and request.user.role not in (
            'admin', 'operations_manager', 'supervisor'
        ):
            return Response(
                {'detail': 'Only supervisors and above can reopen a closed job.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        old_status = job.status
        job.status = new_status

        # Handle assignment if provided (validated User instance); only
        # roles that manage jobs may change the assignee.
        new_assignee = serializer.validated_data.get('assigned_to')
        assignee_changed = (
            'assigned_to' in serializer.validated_data
            and new_assignee is not None
            and new_assignee != job.assigned_to
            and request.user.role in ('operations_manager', 'supervisor')
        )
        if assignee_changed:
            job.assigned_to = new_assignee

        if new_status == Job.Status.CLOSED:
            job.resolution_notes = notes or job.resolution_notes
        if old_status == Job.Status.CLOSED and new_status == Job.Status.OPEN:
            job.closed_at = None

        job.save()

        JobStatusHistory.objects.create(
            job=job, from_status=old_status, to_status=new_status,
            changed_by=request.user, notes=notes,
        )

        log_action(
            user=request.user, action='status_change', entity_type='Job',
            entity_id=job.pk,
            changes={'from': old_status, 'to': new_status, 'notes': notes},
            request=request,
        )

        # Trigger notifications
        from notifications.services import notify_job_status_change, notify_job_assigned
        notify_job_status_change(job, old_status, new_status, request.user)
        if assignee_changed:
            notify_job_assigned(job, assigned_by=request.user)

        return Response(JobDetailSerializer(job, context={'request': request}).data)


class RunSlaCheckView(APIView):
    """Production cron entry point — authenticated by shared secret header."""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from django.conf import settings as django_settings
        secret = django_settings.CRON_SECRET
        if not secret or request.headers.get('X-Cron-Secret') != secret:
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        from .services import escalate_overdue_jobs
        escalated = escalate_overdue_jobs()
        by_company = {}
        for job in escalated:
            slug = job.company.slug if job.company_id else 'unknown'
            by_company[slug] = by_company.get(slug, 0) + 1
        return Response({'escalated': len(escalated), 'by_company': by_company})


class JobAssignView(APIView):
    """Assign or reassign a technician without a status change."""
    permission_classes = [CanManageJobs]

    def post(self, request, pk):
        try:
            job = Job.objects.filter(company_id=request.user.company_id).get(pk=pk)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = JobAssignSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        technician = serializer.validated_data['assigned_to']

        if job.status == Job.Status.CLOSED:
            return Response(
                {'detail': 'Cannot assign a closed job.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if technician == job.assigned_to:
            return Response(
                {'detail': 'Job is already assigned to this technician.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous = job.assigned_to
        job.assigned_to = technician
        old_status = job.status
        if job.status == Job.Status.OPEN:
            job.status = Job.Status.ASSIGNED
        job.save()

        note = (
            f'Reassigned from {previous.get_full_name()} to {technician.get_full_name()}'
            if previous else f'Assigned to {technician.get_full_name()}'
        )
        JobStatusHistory.objects.create(
            job=job, from_status=old_status, to_status=job.status,
            changed_by=request.user, notes=note,
        )
        log_action(
            user=request.user,
            action='reassignment' if previous else 'assignment',
            entity_type='Job', entity_id=job.pk,
            changes={
                'from': previous.get_full_name() if previous else None,
                'to': technician.get_full_name(),
            },
            request=request,
        )
        from notifications.services import notify_job_assigned
        notify_job_assigned(job, assigned_by=request.user)

        return Response(JobDetailSerializer(job, context={'request': request}).data)
