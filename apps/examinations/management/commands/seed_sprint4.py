import random
from datetime import date, time, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject, ClassSubject, Period, TimetableEntry
from apps.students.models import Student
from apps.examinations.models import GradeScale, Exam, ExamSchedule, ExamMarks, ExamStudentResult


class Command(BaseCommand):
    help = "Seed database with Sprint 4 data: Grading scales, Timetable periods & entries, Exam terms, marks, and calculated report cards."

    def handle(self, *args, **options):
        self.stdout.write("[*] Starting Sprint 4 data seeding...")

        with transaction.atomic():
            admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(role='ADMIN').first()
            academic_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
            if not academic_year:
                academic_year, _ = AcademicYear.objects.get_or_create(
                    name="2025-2026",
                    defaults={
                        'start_date': date(2025, 8, 1),
                        'end_date': date(2026, 6, 30),
                        'is_current': True,
                    }
                )

            # -------------------------------------------------------------
            # 1. Grading Scale Tiers
            # -------------------------------------------------------------
            self.stdout.write("[*] 1. Seeding Grading Scale Tiers...")
            grade_tiers = [
                {"name": "A+", "min_percentage": Decimal("90.00"), "max_percentage": Decimal("100.00"), "grade_point": Decimal("4.00"), "remarks": "Outstanding Performance"},
                {"name": "A",  "min_percentage": Decimal("80.00"), "max_percentage": Decimal("89.99"),  "grade_point": Decimal("3.70"), "remarks": "Excellent Mastery"},
                {"name": "B",  "min_percentage": Decimal("70.00"), "max_percentage": Decimal("79.99"),  "grade_point": Decimal("3.00"), "remarks": "Very Good"},
                {"name": "C",  "min_percentage": Decimal("60.00"), "max_percentage": Decimal("69.99"),  "grade_point": Decimal("2.00"), "remarks": "Good / Average"},
                {"name": "D",  "min_percentage": Decimal("50.00"), "max_percentage": Decimal("59.99"),  "grade_point": Decimal("1.50"), "remarks": "Satisfactory / Pass"},
                {"name": "E",  "min_percentage": Decimal("40.00"), "max_percentage": Decimal("49.99"),  "grade_point": Decimal("1.00"), "remarks": "Needs Improvement"},
                {"name": "F",  "min_percentage": Decimal("0.00"),  "max_percentage": Decimal("39.99"),  "grade_point": Decimal("0.00"), "remarks": "Failed"},
            ]
            for tier in grade_tiers:
                GradeScale.objects.update_or_create(
                    name=tier["name"],
                    defaults=tier
                )
            self.stdout.write("    [+] 7 Standard grading scale tiers configured.")

            # -------------------------------------------------------------
            # 2. Daily Academic Periods
            # -------------------------------------------------------------
            self.stdout.write("[*] 2. Seeding Daily Timetable Periods...")
            periods_data = [
                {"name": "Period 1", "start_time": time(8, 0),  "end_time": time(8, 45),  "period_number": 1, "is_break": False},
                {"name": "Period 2", "start_time": time(8, 45), "end_time": time(9, 30),  "period_number": 2, "is_break": False},
                {"name": "Period 3", "start_time": time(9, 30), "end_time": time(10, 15), "period_number": 3, "is_break": False},
                {"name": "Break / Recess", "start_time": time(10, 15), "end_time": time(10, 45), "period_number": 4, "is_break": True},
                {"name": "Period 4", "start_time": time(10, 45), "end_time": time(11, 30), "period_number": 5, "is_break": False},
                {"name": "Period 5", "start_time": time(11, 30), "end_time": time(12, 15), "period_number": 6, "is_break": False},
                {"name": "Period 6", "start_time": time(12, 15), "end_time": time(13, 0),  "period_number": 7, "is_break": False},
                {"name": "Period 7", "start_time": time(13, 0),  "end_time": time(13, 40), "period_number": 8, "is_break": False},
            ]
            created_periods = []
            for p_info in periods_data:
                p_obj, _ = Period.objects.update_or_create(
                    name=p_info["name"],
                    defaults=p_info
                )
                created_periods.append(p_obj)
            self.stdout.write(f"    [+] {len(created_periods)} periods seeded.")

            # -------------------------------------------------------------
            # 3. Timetable Matrix for Active Classes
            # -------------------------------------------------------------
            self.stdout.write("[*] 3. Seeding Weekly Timetable Entries...")
            classes = list(ClassRoom.objects.all()[:4])
            teacher_users = list(User.objects.filter(role__in=['TEACHER', 'ADMIN', 'COORDINATOR']))
            teaching_periods = [p for p in created_periods if not p.is_break]
            days = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']

            entries_count = 0
            for cls in classes:
                sections = cls.sections.all()
                subjects = list(Subject.objects.filter(assigned_classes__class_room=cls).distinct())
                if not subjects:
                    subjects = list(Subject.objects.all()[:5])

                for sec in sections:
                    for day in days:
                        for idx, period in enumerate(teaching_periods):
                            subject = subjects[idx % len(subjects)]
                            teacher_user = teacher_users[idx % len(teacher_users)] if teacher_users else None
                            
                            # Check if teacher is already booked at this day/period
                            if teacher_user and TimetableEntry.objects.filter(teacher=teacher_user, day_of_week=day, period=period).exclude(class_room=cls, section=sec).exists():
                                avail_teachers = [t for t in teacher_users if not TimetableEntry.objects.filter(teacher=t, day_of_week=day, period=period).exists()]
                                teacher_user = avail_teachers[0] if avail_teachers else None

                            TimetableEntry.objects.update_or_create(
                                academic_year=academic_year,
                                class_room=cls,
                                section=sec,
                                day_of_week=day,
                                period=period,
                                defaults={
                                    'subject': subject,
                                    'teacher': teacher_user,
                                    'room_number': f"Room {cls.numeric_level * 10 + 1}",
                                }
                            )
                            entries_count += 1
            self.stdout.write(f"    [+] {entries_count} timetable slots populated.")

            # -------------------------------------------------------------
            # 4. Examination Terms & Date Sheets
            # -------------------------------------------------------------
            self.stdout.write("[*] 4. Seeding Examination Terms & Date Sheets...")
            midterm_exam, _ = Exam.objects.update_or_create(
                title="Mid-Term Assessment 2026",
                academic_year=academic_year,
                defaults={
                    'exam_type': 'MID_TERM',
                    'start_date': date(2026, 3, 10),
                    'end_date': date(2026, 3, 20),
                    'is_published': True,
                    'description': "Official mid-term comprehensive assessment for all academic levels."
                }
            )

            final_exam, _ = Exam.objects.update_or_create(
                title="Annual Final Examinations 2026",
                academic_year=academic_year,
                defaults={
                    'exam_type': 'FINAL_TERM',
                    'start_date': date(2026, 6, 1),
                    'end_date': date(2026, 6, 15),
                    'is_published': False,
                    'description': "End of academic session final examinations."
                }
            )

            # Create schedule papers for classes
            schedules_created = []
            for cls in ClassRoom.objects.all()[:4]:
                subjects = list(Subject.objects.filter(assigned_classes__class_room=cls).distinct())
                if not subjects:
                    subjects = list(Subject.objects.all()[:4])
                
                exam_start_day = date(2026, 3, 10)
                for idx, subj in enumerate(subjects):
                    paper_date = exam_start_day + timedelta(days=idx * 2)
                    sched, _ = ExamSchedule.objects.update_or_create(
                        exam=midterm_exam,
                        class_room=cls,
                        subject=subj,
                        defaults={
                            'exam_date': paper_date,
                            'start_time': time(9, 0),
                            'end_time': time(12, 0),
                            'total_marks': Decimal("100.00"),
                            'passing_marks': Decimal("40.00"),
                            'room_number': f"Hall {cls.numeric_level}",
                        }
                    )
                    schedules_created.append(sched)
            self.stdout.write(f"    [+] {len(schedules_created)} exam date-sheet papers scheduled.")

            # -------------------------------------------------------------
            # 5. Student Exam Marks Entry
            # -------------------------------------------------------------
            self.stdout.write("[*] 5. Seeding Student Exam Marks...")
            marks_count = 0
            all_students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section')

            score_pools = [
                [94, 98, 92, 95, 89, 96],
                [85, 88, 82, 90, 84, 87],
                [76, 78, 72, 80, 75, 79],
                [62, 68, 65, 59, 71, 64],
                [52, 48, 55, 50, 46, 54],
                [35, 38, 42, 30, 44, 38],
            ]

            for cls in ClassRoom.objects.all()[:4]:
                cls_schedules = ExamSchedule.objects.filter(exam=midterm_exam, class_room=cls)
                if not cls_schedules.exists():
                    continue

                cls_students = list(all_students.filter(current_class=cls))
                for s_idx, student in enumerate(cls_students):
                    score_profile = score_pools[s_idx % len(score_pools)]
                    for p_idx, sched in enumerate(cls_schedules):
                        score = score_profile[p_idx % len(score_profile)]
                        score = max(0, min(100, score + random.randint(-3, 3)))
                        
                        ExamMarks.objects.update_or_create(
                            exam_schedule=sched,
                            student=student,
                            defaults={
                                'marks_obtained': Decimal(str(score)),
                                'is_absent': False,
                                'recorded_by': admin_user,
                                'remarks': 'Evaluated'
                            }
                        )
                        marks_count += 1
            self.stdout.write(f"    [+] {marks_count} subject marks recorded.")

            # -------------------------------------------------------------
            # 6. Result Calculation & Positions Computation
            # -------------------------------------------------------------
            self.stdout.write("[*] 6. Calculating Total Marks, Grades, and Class/Section Positions...")
            
            for cls in ClassRoom.objects.all()[:4]:
                cls_schedules = ExamSchedule.objects.filter(exam=midterm_exam, class_room=cls)
                if not cls_schedules.exists():
                    continue
                
                total_max_marks = sum(s.total_marks for s in cls_schedules)
                cls_students = all_students.filter(current_class=cls)

                student_totals = []
                for student in cls_students:
                    marks_qs = ExamMarks.objects.filter(exam_schedule__in=cls_schedules, student=student)
                    obtained = Decimal('0.00')
                    has_fail = False

                    for m in marks_qs:
                        if m.is_absent:
                            has_fail = True
                        else:
                            obtained += m.marks_obtained
                            if m.marks_obtained < m.exam_schedule.passing_marks:
                                has_fail = True

                    pct = (obtained / total_max_marks * Decimal('100.00')) if total_max_marks > 0 else Decimal('0.00')
                    pct = round(pct, 2)

                    grade_str, remarks_str = GradeScale.get_grade_for_percentage(pct)
                    is_passed = (not has_fail) and (pct >= Decimal('40.00'))

                    student_totals.append({
                        'student': student,
                        'section': student.current_section,
                        'total_marks': total_max_marks,
                        'obtained_marks': obtained,
                        'percentage': pct,
                        'grade': grade_str,
                        'grade_remarks': remarks_str,
                        'is_passed': is_passed,
                    })

                # Sort by obtained marks desc to assign class rank
                student_totals.sort(key=lambda x: x['obtained_marks'], reverse=True)
                for class_pos, item in enumerate(student_totals, 1):
                    item['position_in_class'] = class_pos

                # Sort per section to assign section rank
                sections = cls.sections.all()
                for sec in sections:
                    sec_items = [it for it in student_totals if it['section'] == sec]
                    sec_items.sort(key=lambda x: x['obtained_marks'], reverse=True)
                    for sec_pos, item in enumerate(sec_items, 1):
                        item['position_in_section'] = sec_pos

                # Save ExamStudentResult records
                for it in student_totals:
                    if not it['section']:
                        continue
                    ExamStudentResult.objects.update_or_create(
                        exam=midterm_exam,
                        student=it['student'],
                        defaults={
                            'class_room': cls,
                            'section': it['section'],
                            'total_marks': it['total_marks'],
                            'obtained_marks': it['obtained_marks'],
                            'percentage': it['percentage'],
                            'grade': it['grade'],
                            'grade_remarks': it['grade_remarks'],
                            'position_in_section': it.get('position_in_section'),
                            'position_in_class': it.get('position_in_class'),
                            'is_passed': it['is_passed'],
                        }
                    )

            results_count = ExamStudentResult.objects.filter(exam=midterm_exam).count()
            self.stdout.write(f"    [+] {results_count} student result sheets & report cards generated.")

        self.stdout.write(self.style.SUCCESS("[+] Sprint 4 data seeding completed successfully!"))
