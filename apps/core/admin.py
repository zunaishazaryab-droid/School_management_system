from django.contrib import admin
from .models import SchoolSetting, Notification, ActivityLog


@admin.register(SchoolSetting)
class SchoolSettingAdmin(admin.ModelAdmin):
    list_display = ('school_name', 'phone', 'email', 'current_academic_session', 'updated_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'module', 'ip_address')
    list_filter = ('action', 'module', 'created_at')
    search_fields = ('description', 'user__username', 'module')
    readonly_fields = ('user', 'action', 'module', 'description', 'ip_address', 'created_at')
