from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.JobCategoryListCreateView.as_view(), name='job_category_list'),
    path('', views.JobListView.as_view(), name='job_list'),
    path('create/', views.JobCreateView.as_view(), name='job_create'),
    path('<int:pk>/', views.JobDetailView.as_view(), name='job_detail'),
    path('<int:pk>/status/', views.JobStatusUpdateView.as_view(), name='job_status_update'),
    path('<int:pk>/assign/', views.JobAssignView.as_view(), name='job_assign'),
    path('run-sla-check/', views.RunSlaCheckView.as_view(), name='run_sla_check'),
]
