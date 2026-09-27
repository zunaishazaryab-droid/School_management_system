from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_hub_view, name='reports_hub'),
    path('students/', views.student_directory_report_view, name='student_report'),
    path('attendance/', views.attendance_summary_report_view, name='attendance_report'),
    path('fees/', views.fee_financial_report_view, name='fee_report'),
    path('exams/', views.exam_gazette_report_view, name='exam_report'),
    path('teachers/', views.teacher_workload_report_view, name='teacher_report'),
]
