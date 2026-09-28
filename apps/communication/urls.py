from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.announcement_list_view, name='announcement_list'),
    path('announcements/create/', views.announcement_create_view, name='announcement_create'),
    path('announcements/<int:pk>/', views.announcement_detail_view, name='announcement_detail'),
    path('announcements/<int:pk>/edit/', views.announcement_edit_view, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete_view, name='announcement_delete'),
    
    path('broadcast/', views.broadcast_center_view, name='broadcast_center'),
    path('templates/', views.template_list_view, name='template_list'),
    path('templates/<int:pk>/delete/', views.template_delete_view, name='template_delete'),
    path('history/', views.communication_history_view, name='history'),

    # Sprint 8: Automated Gateway & Trigger Engine
    path('gateways/', views.notification_gateway_view, name='gateway_dashboard'),
    path('queue/', views.notification_queue_view, name='queue_monitor'),
    path('queue/dispatch/', views.process_queue_dispatch_action, name='process_queue_dispatch'),
    path('trigger/absence/', views.trigger_absence_alert_engine, name='trigger_absence'),
    path('trigger/fee-overdue/', views.trigger_fee_overdue_engine, name='trigger_fee_overdue'),
]

