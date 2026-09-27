from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('student/', views.student_attendance_view, name='student_attendance'),
    path('teacher/', views.teacher_attendance_view, name='teacher_attendance'),
    path('report/', views.attendance_report_view, name='attendance_report'),
]
