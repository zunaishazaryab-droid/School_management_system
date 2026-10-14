import os
import sys
import django

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject
from apps.students.models import Student
from apps.examinations.models import Exam, ExamSchedule, ExamMarks, ExamStudentResult, GradeScale

def seed_assessment_plan():
    print("🌱 Seeding Yearly Assessment Plan...")
    curr_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    if not curr_year:
        curr_year = AcademicYear.objects.create(name="Academic Session 2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)

    classes = ClassRoom.objects.all()
    subjects = Subject.objects.all()
    students = Student.objects.filter(status='ACTIVE')

    # 1. Weekly Test #1
    w1, _ = Exam.objects.get_or_create(
        title="Weekly Test 1 (Maths & Science)",
        academic_year=curr_year,
        defaults={
            'exam_type': Exam.ExamType.WEEKLY_TEST,
            'start_date': date(2026, 5, 10),
            'end_date': date(2026, 5, 12),
            'is_published': True,
            'is_active': False,
            'description': 'Weekly evaluation test for unit 1 concepts.'
        }
    )

    # 2. Monthly Assessment - May
    m1, _ = Exam.objects.get_or_create(
        title="Monthly Assessment (May 2026)",
        academic_year=curr_year,
        defaults={
            'exam_type': Exam.ExamType.MONTHLY_TEST,
            'start_date': date(2026, 5, 25),
            'end_date': date(2026, 5, 30),
            'is_published': True,
            'is_active': False,
            'description': 'Monthly cumulative assessment for May syllabus.'
        }
    )

    # 3. First Term Examination
    t1, _ = Exam.objects.get_or_create(
        title="First Term Examination 2026",
        academic_year=curr_year,
        defaults={
            'exam_type': Exam.ExamType.FIRST_TERM,
            'start_date': date(2026, 9, 15),
            'end_date': date(2026, 9, 28),
            'is_published': True,
            'is_active': False,
            'description': 'Official 1st Term examination covering 40% syllabus.'
        }
    )

    # 4. Second Term / Mid-Term
    t2, _ = Exam.objects.get_or_create(
        title="Second Term / Mid-Term Examination 2026",
        academic_year=curr_year,
        defaults={
            'exam_type': Exam.ExamType.SECOND_TERM,
            'start_date': date(2026, 12, 10),
            'end_date': date(2026, 12, 22),
            'is_published': True,
            'is_active': True,
            'description': 'Mid-Term comprehensive assessment.'
        }
    )

    # 5. Final Annual Examination
    t3, _ = Exam.objects.get_or_create(
        title="Final Annual Examination 2027",
        academic_year=curr_year,
        defaults={
            'exam_type': Exam.ExamType.FINAL_TERM,
            'start_date': date(2027, 3, 10),
            'end_date': date(2027, 3, 25),
            'is_published': False,
            'is_active': True,
            'description': 'Final annual examination for session 2026-2027.'
        }
    )

    # Ensure schedules and sample marks exist for students in first class
    c1 = classes.first()
    if c1 and subjects.exists():
        for ex in [w1, m1, t1, t2]:
            sub_list = subjects[:3]
            for s in sub_list:
                sch, _ = ExamSchedule.objects.get_or_create(
                    exam=ex,
                    class_room=c1,
                    subject=s,
                    defaults={
                        'exam_date': ex.start_date,
                        'start_time': '09:00',
                        'end_time': '11:00',
                        'total_marks': 50 if ex.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.MONTHLY_TEST] else 100,
                        'passing_marks': 17 if ex.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.MONTHLY_TEST] else 33,
                    }
                )
                for st in Student.objects.filter(current_class=c1):
                    ExamMarks.objects.get_or_create(
                        exam_schedule=sch,
                        student=st,
                        defaults={
                            'marks_obtained': Decimal('42.00') if sch.total_marks == 50 else Decimal('85.00'),
                            'is_absent': False,
                            'remarks': 'Good performance'
                        }
                    )
            
            # Generate overall result
            for st in Student.objects.filter(current_class=c1):
                marks = ExamMarks.objects.filter(exam_schedule__exam=ex, student=st)
                tot_max = sum(m.exam_schedule.total_marks for m in marks)
                tot_obt = sum(m.marks_obtained for m in marks if not m.is_absent)
                pct = (tot_obt / Decimal(str(tot_max)) * Decimal('100')) if tot_max > 0 else Decimal('0')
                grade, rem = GradeScale.get_grade_for_percentage(pct)
                ExamStudentResult.objects.update_or_create(
                    exam=ex,
                    student=st,
                    defaults={
                        'class_room': c1,
                        'section': st.current_section,
                        'total_marks': Decimal(str(tot_max)),
                        'obtained_marks': tot_obt,
                        'percentage': round(pct, 2),
                        'grade': grade,
                        'grade_remarks': rem,
                        'is_passed': pct >= 33,
                        'position_in_section': 1,
                        'position_in_class': 1
                    }
                )

    print("✅ Yearly Assessment Plan seeded with Weekly, Monthly, 1st Term, 2nd Term & Final Term exams!")

if __name__ == '__main__':
    seed_assessment_plan()
