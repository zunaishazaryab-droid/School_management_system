from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.students.models import Student
from apps.attendance.models import StudentAttendance


class AttendanceModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher_user = User.objects.create_user(username='t_user', password='password123', role=User.Role.TEACHER)
        self.year = AcademicYear.objects.create(name='2026-2027', start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
        self.cls = ClassRoom.objects.create(name='Class 5', code='C5', numeric_level=5)
        self.sec = Section.objects.create(class_room=self.cls, name='A')
        self.student = Student.objects.create(
            admission_number='STU-ATT-01',
            first_name='Kashif',
            current_class=self.cls,
            current_section=self.sec,
            academic_year=self.year,
            admission_date=date(2026, 4, 1),
            guardian_name='Saeed',
            guardian_phone='+92 300 1234567',
            residential_address='Address'
        )

    def test_student_attendance_view_get(self):
        self.client.login(username='t_user', password='password123')
        response = self.client.get(reverse('attendance:student_attendance'), {
            'class_id': self.cls.id,
            'section_id': self.sec.id,
            'date': str(date.today())
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kashif')

    def test_student_attendance_save_post(self):
        self.client.login(username='t_user', password='password123')
        response = self.client.post(
            f"{reverse('attendance:student_attendance')}?class_id={self.cls.id}&section_id={self.sec.id}&date={date.today()}",
            {
                f'status_{self.student.id}': 'PRESENT',
                f'remarks_{self.student.id}': 'On time'
            }
        )
        self.assertEqual(response.status_code, 302)
        att = StudentAttendance.objects.filter(student=self.student, date=date.today()).first()
        self.assertIsNotNone(att)
        self.assertEqual(att.status, 'PRESENT')
