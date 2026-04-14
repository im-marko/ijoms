from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.DashboardSummaryView.as_view(), name='dashboard_summary'),
    path('technician-performance/', views.TechnicianPerformanceView.as_view(), name='tech_performance'),
    path('job-volume/', views.JobVolumeView.as_view(), name='job_volume'),
    path('escalation-trends/', views.EscalationTrendsView.as_view(), name='escalation_trends'),
    path('export/jobs/', views.ExportJobsCSVView.as_view(), name='export_jobs_csv'),
]
