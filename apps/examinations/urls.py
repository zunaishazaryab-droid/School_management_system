from django.urls import path
from . import views

app_name = 'examinations'

urlpatterns = [
    path('', views.exam_list_view, name='exam_list'),
    path('create/', views.exam_create_view, name='exam_create'),
    path('<int:pk>/', views.exam_detail_view, name='exam_detail'),
    path('<int:pk>/edit/', views.exam_edit_view, name='exam_edit'),
    path('<int:pk>/delete/', views.exam_delete_view, name='exam_delete'),
    path('<int:pk>/toggle-publish/', views.exam_toggle_publish_view, name='toggle_publish'),
    path('<int:exam_id>/schedule/add/', views.exam_schedule_create_view, name='schedule_create'),
    path('schedule/<int:pk>/delete/', views.exam_schedule_delete_view, name='schedule_delete'),
    path('marks/entry/<int:schedule_id>/', views.exam_marks_entry_view, name='marks_entry'),
    path('<int:exam_id>/marks-entry/', views.exam_direct_marks_entry_view, name='quick_marks_entry'),
    path('<int:exam_id>/calculate/', views.exam_calculate_results_view, name='calculate_results'),
    path('<int:exam_id>/results/class/<int:class_id>/', views.exam_class_result_view, name='class_result'),
    path('<int:exam_id>/class/<int:class_id>/master-marksheet/', views.exam_class_master_marksheet_view, name='class_master_marksheet'),
    path('<int:exam_id>/class/<int:class_id>/auto-schedule/', views.auto_schedule_class_subjects_view, name='auto_schedule_class_subjects'),
    path('<int:exam_id>/report-card/<int:student_id>/', views.student_report_card_view, name='student_report_card'),
    path('report-card/<int:exam_id>/<int:student_id>/', views.student_report_card_view, name='student_report_card_alias'),
    path('<int:exam_id>/student/<int:student_id>/edit-marks/', views.student_marks_edit_view, name='student_marks_edit'),
    path('student-marks/<int:exam_id>/<int:student_id>/', views.student_marks_edit_view, name='student_marks_edit_alias'),
    path('grade-scales/', views.grading_scale_list_view, name='grade_scales'),

    # Sprint 9: Online CBT Assessments
    path('cbt/', views.cbt_assessment_list_view, name='cbt_list'),
    path('cbt/create/', views.cbt_assessment_create_view, name='cbt_create'),
    path('cbt/<int:pk>/questions/', views.cbt_assessment_questions_view, name='cbt_questions'),
    path('cbt/<int:pk>/take/', views.cbt_assessment_take_view, name='cbt_take'),
    path('cbt/<int:pk>/start/', views.cbt_assessment_take_view, name='cbt_start_alias'),
    path('cbt/<int:pk>/results/', views.cbt_assessment_results_view, name='cbt_results'),
]

