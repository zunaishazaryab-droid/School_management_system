from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User
from apps.academics.models import ClassRoom, Subject
from apps.syllabus.models import SyllabusChapter, SyllabusTopic


class SyllabusModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = User.objects.create_user(username='t_syl', password='password123', role=User.Role.TEACHER)
        self.cls = ClassRoom.objects.create(name='Class 9', code='C9', numeric_level=9)
        self.sub = Subject.objects.create(name='Physics', code='PHY-09')
        self.ch = SyllabusChapter.objects.create(class_room=self.cls, subject=self.sub, chapter_number=1, title='Physical Quantities')
        self.top1 = SyllabusTopic.objects.create(chapter=self.ch, topic_number='1.1', title='Base Units', status=SyllabusTopic.Status.COMPLETED)
        self.top2 = SyllabusTopic.objects.create(chapter=self.ch, topic_number='1.2', title='Derived Units', status=SyllabusTopic.Status.NOT_STARTED)

    def test_syllabus_progress_calculation(self):
        self.assertEqual(self.ch.progress_pct, 50)

    def test_syllabus_tracker_view(self):
        self.client.login(username='t_syl', password='password123')
        response = self.client.get(reverse('syllabus:tracker'), {
            'class_id': self.cls.id,
            'subject_id': self.sub.id
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Physical Quantities')
        self.assertContains(response, 'Base Units')

    def test_update_topic_status(self):
        self.client.login(username='t_syl', password='password123')
        response = self.client.post(
            f"{reverse('syllabus:tracker')}?class_id={self.cls.id}&subject_id={self.sub.id}",
            {
                'update_topic_status': '1',
                'topic_id': self.top2.id,
                'new_status': 'COMPLETED'
            }
        )
        self.assertEqual(response.status_code, 302)
        self.top2.refresh_from_db()
        self.assertEqual(self.top2.status, SyllabusTopic.Status.COMPLETED)
        self.assertEqual(self.ch.progress_pct, 100)
