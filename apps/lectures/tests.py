from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from apps.accounts.models import User
from apps.academics.models import ClassRoom, Section, Subject
from apps.lectures.models import DailyLecture, Homework


class LecturesModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(username='t_lect', password='password123', role=User.Role.TEACHER)
        self.cls = ClassRoom.objects.create(name='Class 8', code='C8', numeric_level=8)
        self.sec = Section.objects.create(class_room=self.cls, name='A')
        self.sub = Subject.objects.create(name='Science', code='SCI-08')

    def test_lecture_list_view(self):
        self.client.login(username='t_lect', password='password123')
        response = self.client.get(reverse('lectures:lecture_list'))
        self.assertEqual(response.status_code, 200)

    def test_create_daily_lecture(self):
        self.client.login(username='t_lect', password='password123')
        response = self.client.post(reverse('lectures:lecture_add'), {
            'date': str(date.today()),
            'class_room': self.cls.id,
            'section': self.sec.id,
            'subject': self.sub.id,
            'chapter_name': 'Ch 1 Cells',
            'topic': 'Cell Membrane Structure',
            'learning_objectives': 'Osmosis and diffusion',
            'classwork_description': 'Drew cell diagram',
            'homework_assigned': 'Q 1-4',
            'present_students_count': 30,
            'absent_students_count': 2,
            'copies_checked_count': 30,
            'remarks': 'Good attention'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(DailyLecture.objects.filter(topic='Cell Membrane Structure').exists())
