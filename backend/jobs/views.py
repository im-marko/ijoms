from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import CanViewJobs, CanManageJobs, IsSupervisorOrAbove
from auditlog.mixins import AuditMixin, log_action
from .models import Job, JobCategory, JobStatusHistory
from .serializers import (
    JobListSerializer, JobDetailSerializer, JobCreateSerializer,
    JobCategorySerializer, JobStatusUpdateSerializer,
)
from .filters import JobFilter

User = get_user_model()


class JobCategoryListCreateView(AuditMixin, generics.ListCreateAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = JobCategorySerializer
    audit_entity_type = 'JobCategory'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [CanViewJobs()]
        return [IsSupervisorOrAbove()]


class JobListView(generics.ListAPIView):
    serializer_class = JobListSerializer
    permission_classes = [CanViewJobs]
    filterset_class = JobFilter
    search_fields = ['title', 'reference_number', 'customer_name', 'description']
    ordering_fields = ['created_at', 'priority', 'status', 'sla_deadline']

    def get_queryset(self):
        qs = Job.objects.select_related('category', 'assigned_to', 'created_by')
        if self.request.user.role == 'technician':
            qs = qs.filter(assigned_to=self.request.user)
        return qs


class JobCreateView(AuditMixin, generics.CreateAPIView):
    serializer_class = JobCreateSerializer
    permission_classes = [CanManageJobs]
    audit_entity_type = 'Job'


class JobDetailView(AuditMixin, generics.RetrieveUpdateAPIView):
    serializer_class = JobDetailSerializer
    permission_classes = [CanViewJobs]
    audit_entity_type = 'Job'

    def get_queryset(self):
        qs = Job.objects.select_related('category', 'assigned_to', 'created_by').prefetch_related('status_history')
        if self.request.user.role == 'technician':
            qs = qs.filter(assigned_to=self.request.user)
        return qs


class JobStatusUpdateView(APIView):
    permission_classes = [CanViewJobs]

    def post(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Technicians can only update their own jobs
        if request.user.role == 'technician' and job.assigned_to != request.user:
            return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = JobStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')

        if not job.can_transition_to(new_status):
            return Response(
                {'detail': f'Cannot transition from {job.status} to {new_status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = job.status
        job.status = new_status

        # Handle assignment if provided
        assigned_to_id = serializer.validated_data.get('assigned_to')
        if assigned_to_id:
            job.assigned_to_id = assigned_to_id

        if new_status == Job.Status.CLOSED:
            job.resolution_notes = notes or job.resolution_notes

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

        # Trigger notification
        from notifications.services import notify_job_status_change
        notify_job_status_change(job, old_status, new_status, request.user)

        return Response(JobDetailSerializer(job).data)
