"""
URL configuration for Schoolmanagment project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Core & Dashboard
    path('', include('apps.core.urls', namespace='core')),
    
    # Authentication & User Management
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    
    # Students Management
    path('students/', include('apps.students.urls', namespace='students')),
    
    # Teachers & Staff Management
    path('teachers/', include('apps.teachers.urls', namespace='teachers')),
    
    # Academics (Classes, Sections, Subjects, Timetable)
    path('academics/', include('apps.academics.urls', namespace='academics')),
    
    # Attendance Management
    path('attendance/', include('apps.attendance.urls', namespace='attendance')),
    
    # Lectures & Daily Log
    path('lectures/', include('apps.lectures.urls', namespace='lectures')),
    
    # Syllabus & Tracking
    path('syllabus/', include('apps.syllabus.urls', namespace='syllabus')),
    
    # Fees & Ledgers
    path('fees/', include('apps.fees.urls', namespace='fees')),
    
    # Examinations & Results
    path('examinations/', include('apps.examinations.urls', namespace='examinations')),
    
    # Expenses & Finance
    path('expenses/', include('apps.expenses.urls', namespace='expenses')),
    
    # Communication & Announcements
    path('communication/', include('apps.communication.urls', namespace='communication')),
    
    # Reports & Exports
    path('reports/', include('apps.reports.urls', namespace='reports')),
    
    # REST API & Mobile Endpoints (Sprint 6)
    path('api/v1/', include('apps.api.urls', namespace='api')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
