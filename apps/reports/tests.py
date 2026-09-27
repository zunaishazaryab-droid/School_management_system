from datetime import date
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.students.models import Student


class ReportsCenterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='report_admin',
            email='report_admin@school.local',
            password='password123',
            role='ADMIN'
        )
        self.academic_year = AcademicYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 8, 1),
            end_date=date(2026, 6, 30),
            is_current=True
        )
        self.class_room = ClassRoom.objects.create(
            name="Class 9",
            numeric_level=9
        )
        self.section = Section.objects.create(
            class_room=self.class_room,
            name="A",
            capacity=30
        )
        self.student = Student.objects.create(
            admission_number="ADM-REP-001",
            first_name="Bilal",
            last_name="Saeed",
            gender="MALE",
            admission_date=date(2025, 8, 1),
            date_of_birth=date(2011, 3, 15),
            current_class=self.class_room,
            current_section=self.section,
            academic_year=self.academic_year,
            guardian_name="Saeed Anwar",
            guardian_phone="03123456789",
            residential_address="Street 4, Sector G-10, Islamabad",
            status="ACTIVE"
        )

    def test_reports_hub_view(self):
        self.client.force_login(self.admin)
        res = self.client.get(reverse('reports:reports_hub'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Reports & Analytics Center")
        self.assertContains(res, "Student & Enrollment Reports")
        self.assertContains(res, "Financial & Fee Collection Reports")

    def test_student_directory_report_html_and_csv(self):
        self.client.force_login(self.admin)
        
        # HTML View
        res = self.client.get(reverse('reports:student_report'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Bilal Saeed")

        # CSV Export
        res_csv = self.client.get(reverse('reports:student_report') + '?export=csv')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv['Content-Type'], 'text/csv')
        self.assertIn("ADM-REP-001", res_csv.content.decode('utf-8'))

    def test_attendance_summary_report(self):
        self.client.force_login(self.admin)
        res = self.client.get(reverse('reports:attendance_report'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Monthly Attendance Summary")

    def test_fee_financial_report(self):
        self.client.force_login(self.admin)
        res = self.client.get(reverse('reports:fee_report'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Financial Collections & Revenue Report")

    def test_teacher_workload_report(self):
        self.client.force_login(self.admin)
        res = self.client.get(reverse('reports:teacher_report'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Faculty Workload & Timetable Report")
