from django.core.management.base import BaseCommand
from datetime import date
from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject, ClassSubject
from apps.students.models import Student, StudentDocument, StudentPromotionHistory


class Command(BaseCommand):
    help = 'Seeds initial Academic structure (Classes, Sections, Subjects) and Students for Sprint 1.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Initializing Sprint 1 Data Seed..."))

        # 1. Academic Year
        year, _ = AcademicYear.objects.get_or_create(
            name='2026-2027',
            defaults={
                'start_date': date(2026, 4, 1),
                'end_date': date(2027, 3, 31),
                'is_current': True
            }
        )
        self.stdout.write(self.style.SUCCESS(f"[OK] Academic Year: {year.name}"))

        # 2. Get Teacher user
        teacher = User.objects.filter(role=User.Role.TEACHER).first()
        coordinator = User.objects.filter(role=User.Role.COORDINATOR).first()

        # 3. Create Standard Classes & Sections
        classes_data = [
            {'name': 'Playgroup', 'code': 'PG', 'level': 0, 'sections': ['A', 'B']},
            {'name': 'Nursery', 'code': 'NUR', 'level': 1, 'sections': ['Rose', 'Tulip']},
            {'name': 'Prep', 'code': 'PREP', 'level': 2, 'sections': ['A', 'B']},
            {'name': 'Class 1', 'code': 'C1', 'level': 3, 'sections': ['A', 'B']},
            {'name': 'Class 2', 'code': 'C2', 'level': 4, 'sections': ['A', 'B']},
            {'name': 'Class 3', 'code': 'C3', 'level': 5, 'sections': ['A', 'B']},
            {'name': 'Class 4', 'code': 'C4', 'level': 6, 'sections': ['A', 'B']},
            {'name': 'Class 5', 'code': 'C5', 'level': 7, 'sections': ['A', 'B']},
            {'name': 'Class 6', 'code': 'C6', 'level': 8, 'sections': ['A', 'B']},
            {'name': 'Class 7', 'code': 'C7', 'level': 9, 'sections': ['A', 'B']},
            {'name': 'Class 8', 'code': 'C8', 'level': 10, 'sections': ['A', 'B']},
            {'name': 'Class 9 (Boys)', 'code': '9-BOYS', 'level': 11, 'sections': ['Science-A', 'Computer-B']},
            {'name': 'Class 9 (Girls)', 'code': '9-GIRLS', 'level': 12, 'sections': ['Science-A', 'Computer-B']},
            {'name': 'Class 10 (Boys)', 'code': '10-BOYS', 'level': 13, 'sections': ['Science-A', 'Computer-B']},
            {'name': 'Class 10 (Girls)', 'code': '10-GIRLS', 'level': 14, 'sections': ['Science-A', 'Computer-B']},
        ]

        class_instances = {}
        section_instances = {}

        for c_data in classes_data:
            cls, _ = ClassRoom.objects.get_or_create(
                code=c_data['code'],
                defaults={
                    'name': c_data['name'],
                    'numeric_level': c_data['level'],
                    'description': f"Standard curriculum level for {c_data['name']}."
                }
            )
            class_instances[c_data['code']] = cls

            for s_name in c_data['sections']:
                sec, _ = Section.objects.get_or_create(
                    class_room=cls,
                    name=s_name,
                    defaults={
                        'capacity': 35,
                        'class_teacher': teacher
                    }
                )
                section_instances[f"{c_data['code']}_{s_name}"] = sec

        self.stdout.write(self.style.SUCCESS(f"[OK] Created {len(class_instances)} Classes with Sections."))

        # 4. Create Subjects
        subjects_data = [
            {'name': 'English A', 'code': 'ENG-A', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'English B', 'code': 'ENG-B', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'Urdu A', 'code': 'URD-A', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'Urdu B', 'code': 'URD-B', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'Mathematics', 'code': 'MATH-101', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'General Science', 'code': 'SCI-101', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'Islamiyat / Ethics', 'code': 'ISL-101', 'total': 50, 'pass_m': 17, 'elective': False},
            {'name': 'Computer Science', 'code': 'CS-101', 'total': 100, 'pass_m': 33, 'elective': True},
            {'name': 'Physics', 'code': 'PHY-201', 'total': 100, 'pass_m': 33, 'elective': False},
            {'name': 'Chemistry', 'code': 'CHEM-201', 'total': 100, 'pass_m': 33, 'elective': False},
        ]

        for s_data in subjects_data:
            sub, _ = Subject.objects.get_or_create(
                code=s_data['code'],
                defaults={
                    'name': s_data['name'],
                    'total_marks': s_data['total'],
                    'passing_marks': s_data['pass_m'],
                    'is_elective': s_data['elective'],
                }
            )

        self.stdout.write(self.style.SUCCESS(f"[OK] Created curriculum subjects."))

        # 5. Create Sample Students
        c1 = class_instances['C1']
        c1_sec_a = section_instances['C1_A']
        c1_sec_b = section_instances['C1_B']
        c9_boys = class_instances['9-BOYS']
        c9_boys_sec = section_instances['9-BOYS_Science-A']
        c9_girls = class_instances['9-GIRLS']
        c9_girls_sec = section_instances['9-GIRLS_Science-A']

        sample_students = [
            {
                'admission_number': 'STU-2026-001',
                'roll_number': '101',
                'first_name': 'Ali',
                'last_name': 'Hassan',
                'gender': Student.Gender.MALE,
                'date_of_birth': date(2018, 5, 14),
                'blood_group': 'B+',
                'current_class': c1,
                'current_section': c1_sec_a,
                'guardian_name': 'Muhammad Hassan',
                'guardian_phone': '+92 301 2345678',
                'guardian_cnic': '61101-1122334-1',
                'residential_address': 'House 14, Street 8, G-10/2, Islamabad',
                'city': 'Islamabad',
                'status': Student.Status.ACTIVE
            },
            {
                'admission_number': 'STU-2026-002',
                'roll_number': '102',
                'first_name': 'Ayesha',
                'last_name': 'Malik',
                'gender': Student.Gender.FEMALE,
                'date_of_birth': date(2018, 8, 22),
                'blood_group': 'O+',
                'current_class': c1,
                'current_section': c1_sec_a,
                'guardian_name': 'Malik Usman',
                'guardian_phone': '+92 302 9876543',
                'guardian_cnic': '61101-2233445-2',
                'residential_address': 'Flat 3B, Silver Heights, F-11, Islamabad',
                'city': 'Islamabad',
                'status': Student.Status.ACTIVE
            },
            {
                'admission_number': 'STU-2026-003',
                'roll_number': '103',
                'first_name': 'Hamza',
                'last_name': 'Nadeem',
                'gender': Student.Gender.MALE,
                'date_of_birth': date(2018, 1, 10),
                'blood_group': 'A+',
                'current_class': c1,
                'current_section': c1_sec_b,
                'guardian_name': 'Nadeem Akhtar',
                'guardian_phone': '+92 303 5556677',
                'guardian_cnic': '61101-3344556-3',
                'residential_address': 'House 89, Street 4, I-8/4, Islamabad',
                'city': 'Islamabad',
                'status': Student.Status.ACTIVE
            },
            {
                'admission_number': 'STU-2026-004',
                'roll_number': '901',
                'first_name': 'Zainab',
                'last_name': 'Fatima',
                'gender': Student.Gender.FEMALE,
                'date_of_birth': date(2010, 11, 4),
                'blood_group': 'AB+',
                'current_class': c9_girls,
                'current_section': c9_girls_sec,
                'guardian_name': 'Tariq Mehmood',
                'guardian_phone': '+92 304 8889900',
                'guardian_cnic': '61101-4455667-4',
                'residential_address': 'Plot 23, River View, Rawalpindi',
                'city': 'Rawalpindi',
                'status': Student.Status.ACTIVE
            },
            {
                'admission_number': 'STU-2026-005',
                'roll_number': '902',
                'first_name': 'Bilal',
                'last_name': 'Rehman',
                'gender': Student.Gender.MALE,
                'date_of_birth': date(2010, 3, 19),
                'blood_group': 'O-',
                'current_class': c9_boys,
                'current_section': c9_boys_sec,
                'guardian_name': 'Abdul Rehman',
                'guardian_phone': '+92 305 7771122',
                'guardian_cnic': '61101-5566778-5',
                'residential_address': 'House 102, Bahria Town Phase 4, Rawalpindi',
                'city': 'Rawalpindi',
                'status': Student.Status.ACTIVE
            }
        ]

        for st_data in sample_students:
            st, created = Student.objects.get_or_create(
                admission_number=st_data['admission_number'],
                defaults={
                    **st_data,
                    'academic_year': year,
                    'admission_date': date(2026, 4, 1),
                    'religion': 'Islam',
                    'nationality': 'Pakistani',
                    'medical_notes': 'No known allergies.'
                }
            )
            action = "Admitted" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"[OK] {action} student: {st.get_full_name()} ({st.admission_number})"))

        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Sprint 1 Data Seed completed successfully!"))
