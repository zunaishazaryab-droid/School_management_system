from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.students.models import Student, StudentPromotionHistory


class StudentModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin_s1', password='password123', role=User.Role.ADMIN)
        self.teacher = User.objects.create_user(username='teacher_s1', password='password123', role=User.Role.TEACHER)
        
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            is_current=True
        )
        self.class1 = ClassRoom.objects.create(name='Class 1', code='C1', numeric_level=1)
        self.sec_a = Section.objects.create(class_room=self.class1, name='A', capacity=40)
        self.class2 = ClassRoom.objects.create(name='Class 2', code='C2', numeric_level=2)
        self.sec_b = Section.objects.create(class_room=self.class2, name='A', capacity=40)

        self.student = Student.objects.create(
            admission_number='STU-TEST-01',
            first_name='Zaid',
            last_name='Khan',
            gender=Student.Gender.MALE,
            current_class=self.class1,
            current_section=self.sec_a,
            academic_year=self.year,
            admission_date=date(2026, 4, 1),
            guardian_name='Amir Khan',
            guardian_phone='+92 300 1234567',
            residential_address='Test Address',
            status=Student.Status.ACTIVE
        )

    def test_student_list_authenticated(self):
        self.client.login(username='admin_s1', password='password123')
        response = self.client.get(reverse('students:student_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zaid Khan')
        self.assertContains(response, 'STU-TEST-01')

    def test_student_detail_view(self):
        self.client.login(username='admin_s1', password='password123')
        response = self.client.get(reverse('students:student_detail', args=[self.student.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zaid Khan')
        self.assertContains(response, 'Amir Khan')

    def test_student_card_view(self):
        self.client.login(username='admin_s1', password='password123')
        response = self.client.get(reverse('students:student_card', args=[self.student.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Student ID Card')
        self.assertContains(response, 'STU-TEST-01')

    def test_student_promotion_execution(self):
        self.client.login(username='admin_s1', password='password123')
        response = self.client.post(reverse('students:student_promotion'), {
            'from_class': self.class1.id,
            'to_class': self.class2.id,
            'to_section': self.sec_b.id,
            'target_academic_year': self.year.id,
            'remarks': 'Promoted after passing annual test',
            'selected_students': [self.student.id]
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify student is now in Class 2
        self.student.refresh_from_db()
        self.assertEqual(self.student.current_class, self.class2)
        self.assertEqual(self.student.current_section, self.sec_b)
        
        # Verify promotion history was logged
        self.assertTrue(StudentPromotionHistory.objects.filter(student=self.student).exists())
