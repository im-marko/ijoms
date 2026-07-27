from django.contrib import admin

from .models import Job, JobCategory, JobStatusHistory


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'sla_hours', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'reference_number', 'title', 'status', 'priority',
        'assigned_to', 'sla_deadline',
    ]
    list_filter = ['status', 'priority']
    search_fields = ['reference_number', 'title', 'customer_name']
    readonly_fields = ['reference_number', 'created_at', 'updated_at', 'closed_at']
    raw_id_fields = ['assigned_to', 'created_by']
    date_hierarchy = 'created_at'


@admin.register(JobStatusHistory)
class JobStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['job', 'from_status', 'to_status', 'changed_by', 'created_at']
    list_filter = ['from_status', 'to_status']
    search_fields = ['job__reference_number']
    readonly_fields = ['job', 'from_status', 'to_status', 'changed_by', 'notes', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
