import csv
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsManagerOrAbove, IsSupervisorOrAbove
from . import services


class DashboardSummaryView(APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        return Response({
            'job_summary': services.get_job_summary(),
            'sla_compliance': services.get_sla_compliance(),
        })


class TechnicianPerformanceView(APIView):
    permission_classes = [IsManagerOrAbove]

    def get(self, request):
        return Response(services.get_technician_performance())


class JobVolumeView(APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        period = request.query_params.get('period', 'daily')
        days = int(request.query_params.get('days', '30'))
        return Response(services.get_job_volume_over_time(period, days))


class EscalationTrendsView(APIView):
    permission_classes = [IsSupervisorOrAbove]

    def get(self, request):
        days = int(request.query_params.get('days', '90'))
        return Response(services.get_escalation_trends(days))


class ExportJobsCSVView(APIView):
    permission_classes = [IsManagerOrAbove]

    def get(self, request):
        from jobs.models import Job
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Reference', 'Title', 'Category', 'Priority', 'Status',
            'Assigned To', 'Customer', 'SLA Deadline', 'Created', 'Closed',
        ])
        jobs = Job.objects.select_related('category', 'assigned_to').all()

        status_filter = request.query_params.get('status')
        if status_filter:
            jobs = jobs.filter(status=status_filter)

        for job in jobs:
            writer.writerow([
                job.reference_number, job.title,
                job.category.name if job.category else '',
                job.priority, job.status,
                job.assigned_to.get_full_name() if job.assigned_to else '',
                job.customer_name, job.sla_deadline, job.created_at, job.closed_at or '',
            ])
        return response
