from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    
    # Notifications & Alerts
    path('notifications/', views.notifications_list_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read_view, name='mark_all_notifications_read'),
    
    # Global Multi-Entity Search
    path('search/', views.global_search_view, name='global_search'),
    
    # Audit Trail & Activity Logs
    path('activity-logs/', views.activity_logs_view, name='activity_logs'),
    
    # School Profile & General Settings
    path('settings/school/', views.school_settings_view, name='school_settings'),
    
    # Staff Users & Role Management
    path('settings/users/', views.user_management_view, name='user_management'),
    path('settings/users/add/', views.user_create_view, name='user_create'),
    path('settings/users/<int:pk>/toggle-status/', views.user_toggle_status_view, name='user_toggle_status'),
    
    # Database Backup & Recovery
    path('settings/backup/', views.database_backup_view, name='database_backup'),
    path('settings/backup/download/', views.database_download_view, name='database_download'),

    # Sprint 9: Multi-Campus & QR Verification
    path('campuses/', views.campus_list_view, name='campus_list'),
    path('campuses/switch/<int:branch_id>/', views.switch_campus_view, name='switch_campus'),
    path('verify-badge/<str:token>/', views.verify_badge_view, name='verify_badge'),
    path('security/scanner/', views.badge_scanner_view, name='badge_scanner'),
]

