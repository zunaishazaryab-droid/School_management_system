from django.core.management.base import BaseCommand
from datetime import date
from decimal import Decimal
from apps.accounts.models import User
from apps.academics.models import ClassRoom, Section, Subject
from apps.students.models import Student
from apps.teachers.models import Teacher, SalaryPayment, StaffLeave, TeacherPerformance
from apps.attendance.models import StudentAttendance, TeacherAttendance
from apps.lectures.models import DailyLecture, Homework
from apps.syllabus.models import SyllabusChapter, SyllabusTopic


class Command(BaseCommand):
    help = 'Seeds initial Teachers, Attendance, Lectures, Syllabus and Homework for Sprint 2.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Initializing Sprint 2 Data Seed..."))

        # 1. Ensure Teacher Users & Profiles
        teachers_data = [
            {
                'username': 'teacher_ahmed',
                'first_name': 'Ahmed',
                'last_name': 'Bilal',
                'email': 'ahmed.bilal@beaconheights.edu.pk',
                'employee_id': 'EMP-2026-001',
                'designation': Teacher.Designation.SUBJECT_SPECIALIST,
                'department': 'Mathematics',
                'qualification': 'M.Sc Mathematics, B.Ed',
                'experience_years': 6,
                'basic_salary': Decimal('55000.00'),
                'phone_number': '+92 300 4445566',
                'residential_address': 'Sector G-9/1, Islamabad'
            },
            {
                'username': 'teacher_sadia',
                'first_name': 'Sadia',
                'last_name': 'Kamran',
                'email': 'sadia.kamran@beaconheights.edu.pk',
                'employee_id': 'EMP-2026-002',
                'designation': Teacher.Designation.SENIOR_TEACHER,
                'department': 'English Literature',
                'qualification': 'M.A English, M.Ed',
                'experience_years': 8,
                'basic_salary': Decimal('60000.00'),
                'phone_number': '+92 301 5556677',
                'residential_address': 'Sector F-8/3, Islamabad'
            },
            {
                'username': 'teacher_usman',
                'first_name': 'Usman',
                'last_name': 'Tariq',
                'email': 'usman.tariq@beaconheights.edu.pk',
                'employee_id': 'EMP-2026-003',
                'designation': Teacher.Designation.SUBJECT_SPECIALIST,
                'department': 'Computer Science',
                'qualification': 'BS Computer Science',
                'experience_years': 4,
                'basic_salary': Decimal('50000.00'),
                'phone_number': '+92 302 6667788',
                'residential_address': 'Sector I-8/2, Islamabad'
            }
        ]

        teacher_objs = []
        for t_data in teachers_data:
            user, _ = User.objects.get_or_create(
                username=t_data['username'],
                defaults={
                    'email': t_data['email'],
                    'first_name': t_data['first_name'],
                    'last_name': t_data['last_name'],
                    'role': User.Role.TEACHER
                }
            )
            user.set_password('teacher123')
            user.save()

            teacher, _ = Teacher.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': t_data['employee_id'],
                    'designation': t_data['designation'],
                    'department': t_data['department'],
                    'qualification': t_data['qualification'],
                    'experience_years': t_data['experience_years'],
                    'joining_date': date(2024, 8, 15),
                    'basic_salary': t_data['basic_salary'],
                    'phone_number': t_data['phone_number'],
                    'residential_address': t_data['residential_address']
                }
            )
            teacher_objs.append(teacher)

        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(teacher_objs)} Teacher Profiles."))

        # 2. Seed Salary Records
        for t in teacher_objs:
            SalaryPayment.objects.get_or_create(
                teacher=t,
                salary_month='April 2026',
                defaults={
                    'basic_salary': t.basic_salary,
                    'allowances': Decimal('5000.00'),
                    'deductions': Decimal('1500.00'),
                    'payment_date': date(2026, 4, 30),
                    'payment_method': SalaryPayment.PaymentMethod.BANK_TRANSFER,
                    'status': SalaryPayment.Status.PAID
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Seeded salary disbursements."))

        # 3. Seed Student Daily Attendance
        c1 = ClassRoom.objects.filter(code='C1').first()
        if c1:
            sec_a = c1.sections.filter(name='A').first()
            if sec_a:
                students = Student.objects.filter(current_class=c1, current_section=sec_a)
                for idx, st in enumerate(students):
                    status_choice = StudentAttendance.Status.ABSENT if idx == 1 else StudentAttendance.Status.PRESENT
                    StudentAttendance.objects.get_or_create(
                        date=date.today(),
                        student=st,
                        defaults={
                            'class_room': c1,
                            'section': sec_a,
                            'status': status_choice,
                            'recorded_by': user
                        }
                    )
        self.stdout.write(self.style.SUCCESS("[OK] Seeded student attendance register."))

        # 4. Seed Daily Lectures & Homework
        math_sub = Subject.objects.filter(code='MATH-101').first()
        if c1 and sec_a and math_sub:
            DailyLecture.objects.get_or_create(
                date=date.today(),
                class_room=c1,
                section=sec_a,
                subject=math_sub,
                teacher=teacher_objs[0].user,
                defaults={
                    'chapter_name': 'Chapter 1: Whole Numbers & Operations',
                    'topic': 'Multi-digit Addition & Subtraction Techniques',
                    'learning_objectives': 'Students understand carryover addition and borrowing in subtraction.',
                    'classwork_description': 'Solved Textbook Page 14 Exercises 1.1 to 1.8 on whiteboard.',
                    'homework_assigned': 'Page 15 Questions 9 to 15 on homework register.',
                    'present_students_count': 18,
                    'absent_students_count': 2,
                    'copies_checked_count': 18,
                    'remarks': 'Pacing was smooth. Most students grasp concept quickly.'
                }
            )

            Homework.objects.get_or_create(
                class_room=c1,
                section=sec_a,
                subject=math_sub,
                teacher=teacher_objs[0].user,
                title='Math Exercise 1.2 — Word Problems',
                defaults={
                    'description': 'Complete word problems 1 to 6 on homework notebook. Show complete calculation steps.',
                    'assigned_date': date.today(),
                    'due_date': date.today(),
                    'status': Homework.Status.ACTIVE
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Seeded Daily Lecture and Homework diary."))

        # 5. Seed Syllabus Hierarchy
        if c1 and math_sub:
            ch1, _ = SyllabusChapter.objects.get_or_create(
                class_room=c1,
                subject=math_sub,
                chapter_number=1,
                defaults={
                    'title': 'Whole Numbers and Place Values',
                    'description': 'Fundamental number system and arithmetic operators.'
                }
            )
            SyllabusTopic.objects.get_or_create(chapter=ch1, topic_number='1.1', defaults={'title': 'Place values up to Millions', 'status': SyllabusTopic.Status.COMPLETED})
            SyllabusTopic.objects.get_or_create(chapter=ch1, topic_number='1.2', defaults={'title': 'Multi-digit Addition & Carryover', 'status': SyllabusTopic.Status.COMPLETED})
            SyllabusTopic.objects.get_or_create(chapter=ch1, topic_number='1.3', defaults={'title': 'Multi-digit Subtraction with Borrowing', 'status': SyllabusTopic.Status.IN_PROGRESS})
            SyllabusTopic.objects.get_or_create(chapter=ch1, topic_number='1.4', defaults={'title': 'Word Problems & Real-world Applications', 'status': SyllabusTopic.Status.NOT_STARTED})

        self.stdout.write(self.style.SUCCESS("[OK] Seeded Syllabus chapter and topics."))
        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Sprint 2 Data Seed completed successfully!"))
