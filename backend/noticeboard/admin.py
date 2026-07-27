from django.contrib import admin

from .models import Notice


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'is_active', 'expiry_date', 'created_by', 'created_at']
    list_filter = ['priority', 'is_active']
    search_fields = ['title', 'content']
    raw_id_fields = ['created_by']
