from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Company, User


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'invite_code', 'created_at']
    search_fields = ['name', 'slug', 'invite_code']
    readonly_fields = ['created_at']


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ['email', 'username', 'first_name', 'last_name', 'role', 'company', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff', 'company']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Company & role', {'fields': ('company', 'role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'first_name', 'last_name',
                'company', 'role', 'phone', 'password1', 'password2',
            ),
        }),
    )
