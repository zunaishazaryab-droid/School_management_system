from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject, ClassSubject


class AcademicsModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.coordinator = User.objects.create_user(username='coord_test', password='password123', role=User.Role.COORDINATOR)
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            is_current=True
        )

    def test_class_list_view(self):
        self.client.login(username='coord_test', password='password123')
        response = self.client.get(reverse('academics:class_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Classes & Sections Management')

    def test_create_class_and_section(self):
        self.client.login(username='coord_test', password='password123')
        response = self.client.post(reverse('academics:class_list'), {
            'action': 'add_class',
            'name': 'Grade 7',
            'code': 'G7',
            'numeric_level': 7,
            'description': 'Middle school grade 7'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ClassRoom.objects.filter(code='G7').exists())

    def test_subject_list_view(self):
        self.client.login(username='coord_test', password='password123')
        response = self.client.get(reverse('academics:subject_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subjects & Academic Curriculum')
