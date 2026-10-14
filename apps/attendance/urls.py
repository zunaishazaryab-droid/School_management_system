from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.student_attendance_view, name='index'),
    path('student/', views.student_attendance_view, name='student_attendance'),
    path('student/<int:student_id>/yearly-log/', views.student_yearly_attendance_view, name='student_yearly_attendance'),
    path('teacher/', views.teacher_attendance_view, name='teacher_attendance'),
    path('report/', views.attendance_report_view, name='attendance_report'),
    
    # Biometric Sync Hub
    path('biometric/', views.biometric_dashboard_view, name='biometric_dashboard'),
    path('biometric/sync/<int:device_id>/', views.biometric_sync_action_view, name='biometric_sync_action'),
    
    # Student Leaves
    path('leaves/', views.leave_request_list_view, name='leave_list'),
    path('leaves/apply/', views.submit_leave_request_view, name='submit_leave'),
    path('leaves/<int:leave_id>/<str:action>/', views.process_leave_request_view, name='process_leave'),
]

