from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['type', 'status', 'recipient', 'subject', 'read', 'created_at']
    list_filter = ['type', 'status', 'read']
    search_fields = ['subject', 'recipient__email']
    raw_id_fields = ['recipient', 'related_job']
    date_hierarchy = 'created_at'
