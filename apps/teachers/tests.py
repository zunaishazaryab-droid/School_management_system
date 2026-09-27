from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal
from apps.accounts.models import User
from apps.teachers.models import Teacher, SalaryPayment, StaffLeave


class TeachersModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(username='admin_t', password='password123', role=User.Role.ADMIN)
        self.user = User.objects.create_user(username='t_bilal', password='password123', role=User.Role.TEACHER)
        self.teacher = Teacher.objects.create(
            user=self.user,
            employee_id='EMP-TEST-01',
            designation=Teacher.Designation.SUBJECT_SPECIALIST,
            qualification='M.Sc',
            joining_date=date(2025, 1, 1),
            basic_salary=Decimal('50000.00'),
            phone_number='+92 300 1122334',
            residential_address='Test Address'
        )

    def test_teacher_list_authenticated(self):
        self.client.login(username='admin_t', password='password123')
        response = self.client.get(reverse('teachers:teacher_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EMP-TEST-01')

    def test_teacher_detail_view(self):
        self.client.login(username='admin_t', password='password123')
        response = self.client.get(reverse('teachers:teacher_detail', args=[self.teacher.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EMP-TEST-01')

    def test_salary_calculation(self):
        sal = SalaryPayment.objects.create(
            teacher=self.teacher,
            salary_month='April 2026',
            basic_salary=Decimal('50000.00'),
            allowances=Decimal('5000.00'),
            deductions=Decimal('2000.00')
        )
        self.assertEqual(sal.net_salary, Decimal('53000.00'))
