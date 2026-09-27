from datetime import date, time
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject
from apps.students.models import Student
from apps.examinations.models import GradeScale, Exam, ExamSchedule, ExamMarks, ExamStudentResult


class ExaminationsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='exam_admin',
            email='exam_admin@school.local',
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
            name="Class 10",
            numeric_level=10
        )
        self.section = Section.objects.create(
            class_room=self.class_room,
            name="A",
            capacity=30
        )
        self.subject1 = Subject.objects.create(
            name="Mathematics",
            code="MATH-10",
            total_marks=100,
            passing_marks=40
        )
        self.subject2 = Subject.objects.create(
            name="English",
            code="ENG-10",
            total_marks=100,
            passing_marks=40
        )

        self.student1 = Student.objects.create(
            admission_number="ADM-EXAM-001",
            first_name="Ali",
            last_name="Khan",
            gender="MALE",
            admission_date=date(2025, 8, 1),
            date_of_birth=date(2010, 5, 12),
            current_class=self.class_room,
            current_section=self.section,
            academic_year=self.academic_year,
            guardian_name="Tariq Khan",
            guardian_phone="03001234567",
            residential_address="House 12, Street 3, Islamabad",
            status="ACTIVE"
        )
        self.student2 = Student.objects.create(
            admission_number="ADM-EXAM-002",
            first_name="Sara",
            last_name="Ahmed",
            gender="FEMALE",
            admission_date=date(2025, 8, 1),
            date_of_birth=date(2010, 8, 20),
            current_class=self.class_room,
            current_section=self.section,
            academic_year=self.academic_year,
            guardian_name="Rashid Ahmed",
            guardian_phone="03007654321",
            residential_address="House 45, Street 8, Islamabad",
            status="ACTIVE"
        )

        # Create standard grade scale
        GradeScale.objects.create(name="A+", min_percentage=Decimal("90.00"), max_percentage=Decimal("100.00"), grade_point=Decimal("4.00"), remarks="Outstanding")
        GradeScale.objects.create(name="A", min_percentage=Decimal("80.00"), max_percentage=Decimal("89.99"), grade_point=Decimal("3.70"), remarks="Excellent")
        GradeScale.objects.create(name="B", min_percentage=Decimal("70.00"), max_percentage=Decimal("79.99"), grade_point=Decimal("3.00"), remarks="Very Good")
        GradeScale.objects.create(name="F", min_percentage=Decimal("0.00"), max_percentage=Decimal("39.99"), grade_point=Decimal("0.00"), remarks="Fail")

        self.exam = Exam.objects.create(
            title="Mid-Term Assessment 2026",
            academic_year=self.academic_year,
            exam_type="MID_TERM",
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 20),
            is_published=True
        )
        self.schedule1 = ExamSchedule.objects.create(
            exam=self.exam,
            class_room=self.class_room,
            subject=self.subject1,
            exam_date=date(2026, 3, 10),
            start_time=time(9, 0),
            end_time=time(12, 0),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("40.00")
        )
        self.schedule2 = ExamSchedule.objects.create(
            exam=self.exam,
            class_room=self.class_room,
            subject=self.subject2,
            exam_date=date(2026, 3, 12),
            start_time=time(9, 0),
            end_time=time(12, 0),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("40.00")
        )

    def test_exam_models_and_marks(self):
        # Record marks for student 1
        m1 = ExamMarks.objects.create(
            exam_schedule=self.schedule1,
            student=self.student1,
            marks_obtained=Decimal("95.00"),
            recorded_by=self.admin
        )
        self.assertEqual(m1.percentage, Decimal("95.00"))

        m2 = ExamMarks.objects.create(
            exam_schedule=self.schedule2,
            student=self.student1,
            marks_obtained=Decimal("85.00"),
            recorded_by=self.admin
        )
        self.assertEqual(m2.percentage, Decimal("85.00"))

    def test_exam_views_accessible(self):
        self.client.force_login(self.admin)
        
        # Exam list
        res = self.client.get(reverse('examinations:exam_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Mid-Term Assessment 2026")

        # Exam detail
        res = self.client.get(reverse('examinations:exam_detail', kwargs={'pk': self.exam.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Mathematics")

        # Grading scales view
        res = self.client.get(reverse('examinations:grade_scales'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "A+")

    def test_marks_entry_and_calculate_results(self):
        self.client.force_login(self.admin)

        # Post marks for schedule 1
        post_data = {
            f'marks_{self.student1.pk}': '92.00',
            f'remarks_{self.student1.pk}': 'Great job',
            f'marks_{self.student2.pk}': '78.00',
            f'remarks_{self.student2.pk}': 'Good effort',
        }
        res = self.client.post(reverse('examinations:marks_entry', kwargs={'schedule_id': self.schedule1.pk}), data=post_data)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ExamMarks.objects.filter(exam_schedule=self.schedule1).count(), 2)

        # Post marks for schedule 2
        post_data2 = {
            f'marks_{self.student1.pk}': '96.00',
            f'remarks_{self.student1.pk}': '',
            f'marks_{self.student2.pk}': '82.00',
            f'remarks_{self.student2.pk}': '',
        }
        self.client.post(reverse('examinations:marks_entry', kwargs={'schedule_id': self.schedule2.pk}), data=post_data2)

        # Trigger Result Calculation
        calc_url = reverse('examinations:calculate_results', kwargs={'exam_id': self.exam.pk})
        res = self.client.post(calc_url, data={'class_id': self.class_room.pk})
        self.assertEqual(res.status_code, 302)

        # Check calculated ExamStudentResult
        res1 = ExamStudentResult.objects.get(exam=self.exam, student=self.student1)
        self.assertEqual(res1.obtained_marks, Decimal("188.00"))
        self.assertEqual(res1.total_marks, Decimal("200.00"))
        self.assertEqual(res1.percentage, Decimal("94.00"))
        self.assertEqual(res1.grade, "A+")
        self.assertEqual(res1.position_in_section, 1)

        res2 = ExamStudentResult.objects.get(exam=self.exam, student=self.student2)
        self.assertEqual(res2.obtained_marks, Decimal("160.00"))
        self.assertEqual(res2.percentage, Decimal("80.00"))
        self.assertEqual(res2.grade, "A")
        self.assertEqual(res2.position_in_section, 2)

        # Report card view test
        rc_res = self.client.get(reverse('examinations:student_report_card', kwargs={'exam_id': self.exam.pk, 'student_id': self.student1.pk}))
        self.assertEqual(rc_res.status_code, 200)
        self.assertContains(rc_res, "Report Card")
        self.assertContains(rc_res, "Ali Khan")
        self.assertContains(rc_res, "94.00%")
