from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.db.models import Q

from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.attendance.models import StudentAttendance
from apps.lectures.models import Homework
from apps.fees.models import FeeInvoice
from apps.examinations.models import ExamStudentResult
from apps.communication.models import Announcement

from .serializers import (
    StudentSerializer, TeacherSerializer, AttendanceSerializer,
    HomeworkSerializer, FeeInvoiceSerializer, ExamResultSerializer,
    AnnouncementSerializer
)


class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for student directory & profile query"""
    queryset = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section')
    serializer_class = StudentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.query_params.get('search', '').strip()
        class_id = self.request.query_params.get('class_id')
        if query:
            qs = qs.filter(Q(first_name__icontains=query) | Q(admission_number__icontains=query))
        if class_id:
            qs = qs.filter(current_class_id=class_id)
        return qs


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for faculty & staff directory"""
    queryset = Teacher.objects.filter(status='ACTIVE').select_related('user')
    serializer_class = TeacherSerializer


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for student attendance query"""
    queryset = StudentAttendance.objects.select_related('student')
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        date = self.request.query_params.get('date')
        student_id = self.request.query_params.get('student_id')
        if date:
            qs = qs.filter(date=date)
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs[:100]


class HomeworkViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for daily homework diary"""
    queryset = Homework.objects.select_related('subject', 'class_room').order_by('-assigned_date')
    serializer_class = HomeworkSerializer


class FeeInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for fee challans & balances"""
    queryset = FeeInvoice.objects.select_related('student', 'class_room').order_by('-due_date')
    serializer_class = FeeInvoiceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs


class ExamResultViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for student examination marks and gazettes"""
    queryset = ExamStudentResult.objects.select_related('student', 'exam').order_by('-percentage')
    serializer_class = ExamResultSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        if student_id:
            qs = qs.filter(student_id=student_id)
        return qs


class AnnouncementViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for circulars and notices feed"""
    queryset = Announcement.objects.filter(is_published=True).select_related('author').order_by('-publish_date')
    serializer_class = AnnouncementSerializer


def api_explorer_view(request):
    """Interactive API Documentation & Endpoint testing explorer"""
    endpoints = [
        {
            'path': '/api/v1/students/',
            'method': 'GET',
            'desc': 'Returns active student records with class, section, guardian details. Supports ?search=Ali&class_id=1',
        },
        {
            'path': '/api/v1/teachers/',
            'method': 'GET',
            'desc': 'Returns faculty members, employee IDs, designations and departments.',
        },
        {
            'path': '/api/v1/attendance/',
            'method': 'GET',
            'desc': 'Returns student daily attendance register records. Filter with ?date=2026-09-28&student_id=1',
        },
        {
            'path': '/api/v1/homework/',
            'method': 'GET',
            'desc': 'Returns active homework diary tasks and submission due dates.',
        },
        {
            'path': '/api/v1/fees/',
            'method': 'GET',
            'desc': 'Returns fee challans, payable totals, and remaining dues. Filter with ?student_id=1',
        },
        {
            'path': '/api/v1/exams/results/',
            'method': 'GET',
            'desc': 'Returns calculated exam percentage, grade points, pass/fail status and class positions.',
        },
        {
            'path': '/api/v1/announcements/',
            'method': 'GET',
            'desc': 'Returns published circular notices, urgent alerts, and event updates.',
        },
    ]
    return render(request, 'api/api_explorer.html', {
        'endpoints': endpoints,
        'page_title': 'REST API Reference & Mobile Endpoints'
    })
