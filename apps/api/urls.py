from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'api'

router = DefaultRouter()
router.register(r'students', views.StudentViewSet, basename='student')
router.register(r'teachers', views.TeacherViewSet, basename='teacher')
router.register(r'attendance', views.AttendanceViewSet, basename='attendance')
router.register(r'homework', views.HomeworkViewSet, basename='homework')
router.register(r'fees', views.FeeInvoiceViewSet, basename='fee')
router.register(r'exams/results', views.ExamResultViewSet, basename='exam_result')
router.register(r'announcements', views.AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path('docs/', views.api_explorer_view, name='docs'),
    path('', include(router.urls)),
]
