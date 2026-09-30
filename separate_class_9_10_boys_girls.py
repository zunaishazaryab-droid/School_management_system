import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.academics.models import ClassRoom, Section, Subject, ClassSubject, TimetableEntry
from apps.students.models import Student, StudentPromotionHistory
from apps.accounts.models import User
from apps.lectures.models import DailyLecture, Homework
from apps.examinations.models import ExamSchedule, OnlineAssessment
from apps.fees.models import FeeStructure, FeeInvoice
from apps.attendance.models import StudentAttendance

teacher = User.objects.filter(role=User.Role.TEACHER).first() or User.objects.filter(role=User.Role.ADMIN).first()

# 1. Create Class 9 (Boys), Class 9 (Girls), Class 10 (Boys), Class 10 (Girls)
classes_info = [
    {
        'name': 'Class 9 (Boys)',
        'code': '9-BOYS',
        'level': 11,
        'description': 'Secondary Metric - Boys Wing',
        'sections': ['Science-A', 'Computer-B']
    },
    {
        'name': 'Class 9 (Girls)',
        'code': '9-GIRLS',
        'level': 12,
        'description': 'Secondary Metric - Girls Wing',
        'sections': ['Science-A', 'Computer-B']
    },
    {
        'name': 'Class 10 (Boys)',
        'code': '10-BOYS',
        'level': 13,
        'description': 'Senior Metric - Boys Wing',
        'sections': ['Science-A', 'Computer-B']
    },
    {
        'name': 'Class 10 (Girls)',
        'code': '10-GIRLS',
        'level': 14,
        'description': 'Senior Metric - Girls Wing',
        'sections': ['Science-A', 'Computer-B']
    },
]

created_classes = {}
for c in classes_info:
    cls, _ = ClassRoom.objects.get_or_create(
        code=c['code'],
        defaults={
            'name': c['name'],
            'numeric_level': c['level'],
            'description': c['description']
        }
    )
    cls.name = c['name']
    cls.numeric_level = c['level']
    cls.description = c['description']
    cls.save()
    created_classes[c['code']] = cls

    for s_name in c['sections']:
        Section.objects.get_or_create(
            class_room=cls,
            name=s_name,
            defaults={'capacity': 35, 'class_teacher': teacher}
        )

# Assign subjects
all_subjects = Subject.objects.all()
for cls in created_classes.values():
    for sub in all_subjects:
        if not ClassSubject.objects.filter(class_room=cls, section=None, subject=sub).exists():
            ClassSubject.objects.create(class_room=cls, section=None, subject=sub, teacher=teacher)
        for sec in cls.sections.all():
            if not ClassSubject.objects.filter(class_room=cls, section=sec, subject=sub).exists():
                ClassSubject.objects.create(class_room=cls, section=sec, subject=sub, teacher=teacher)

# Migrate students from old Class 9
old_c9 = ClassRoom.objects.filter(code='C9').first()
if old_c9:
    for st in Student.objects.filter(current_class=old_c9):
        target_cls = created_classes['9-BOYS'] if st.gender == Student.Gender.MALE else created_classes['9-GIRLS']
        sec_name = st.current_section.name if st.current_section else 'Science-A'
        target_sec = target_cls.sections.filter(name=sec_name).first() or target_cls.sections.first()
        st.current_class = target_cls
        st.current_section = target_sec
        st.save()
        print(f"Migrated Student {st.get_full_name()} ({st.gender}) to {target_cls.name} ({target_sec.name})")

    # Reassign sections & invoices
    c9_boys_sec = created_classes['9-BOYS'].sections.first()
    for sec in list(old_c9.sections.all()):
        FeeInvoice.objects.filter(section=sec).update(section=c9_boys_sec)
        StudentAttendance.objects.filter(section=sec).update(section=c9_boys_sec)
        sec.delete()

    DailyLecture.objects.filter(class_room=old_c9).update(class_room=created_classes['9-BOYS'])
    Homework.objects.filter(class_room=old_c9).update(class_room=created_classes['9-BOYS'])
    ExamSchedule.objects.filter(class_room=old_c9).update(class_room=created_classes['9-BOYS'])
    OnlineAssessment.objects.filter(class_room=old_c9).update(class_room=created_classes['9-BOYS'])
    FeeStructure.objects.filter(class_room=old_c9).update(class_room=created_classes['9-BOYS'])
    FeeInvoice.objects.filter(class_room=old_c9).update(class_room=created_classes['9-BOYS'])
    StudentPromotionHistory.objects.filter(from_class=old_c9).update(from_class=created_classes['9-BOYS'])
    StudentPromotionHistory.objects.filter(to_class=old_c9).update(to_class=created_classes['9-BOYS'])
    TimetableEntry.objects.filter(class_room=old_c9).delete()
    ClassSubject.objects.filter(class_room=old_c9).delete()
    old_c9.delete()
    print("Deleted old Class 9 (C9)")

# Migrate any old Class 10
old_c10 = ClassRoom.objects.filter(code='C10').first()
if old_c10:
    for st in Student.objects.filter(current_class=old_c10):
        target_cls = created_classes['10-BOYS'] if st.gender == Student.Gender.MALE else created_classes['10-GIRLS']
        sec_name = st.current_section.name if st.current_section else 'Science-A'
        target_sec = target_cls.sections.filter(name=sec_name).first() or target_cls.sections.first()
        st.current_class = target_cls
        st.current_section = target_sec
        st.save()
        print(f"Migrated Student {st.get_full_name()} ({st.gender}) to {target_cls.name} ({target_sec.name})")

    c10_boys_sec = created_classes['10-BOYS'].sections.first()
    for sec in list(old_c10.sections.all()):
        FeeInvoice.objects.filter(section=sec).update(section=c10_boys_sec)
        StudentAttendance.objects.filter(section=sec).update(section=c10_boys_sec)
        sec.delete()

    DailyLecture.objects.filter(class_room=old_c10).update(class_room=created_classes['10-BOYS'])
    Homework.objects.filter(class_room=old_c10).update(class_room=created_classes['10-BOYS'])
    ExamSchedule.objects.filter(class_room=old_c10).update(class_room=created_classes['10-BOYS'])
    OnlineAssessment.objects.filter(class_room=old_c10).update(class_room=created_classes['10-BOYS'])
    FeeStructure.objects.filter(class_room=old_c10).update(class_room=created_classes['10-BOYS'])
    FeeInvoice.objects.filter(class_room=old_c10).update(class_room=created_classes['10-BOYS'])
    StudentPromotionHistory.objects.filter(from_class=old_c10).update(from_class=created_classes['10-BOYS'])
    StudentPromotionHistory.objects.filter(to_class=old_c10).update(to_class=created_classes['10-BOYS'])
    TimetableEntry.objects.filter(class_room=old_c10).delete()
    ClassSubject.objects.filter(class_room=old_c10).delete()
    old_c10.delete()
    print("Deleted old Class 10 (C10)")

print("\n--- ALL CLASSES IN DATABASE ---")
for c in ClassRoom.objects.all().order_by('numeric_level'):
    secs = [s.name for s in c.sections.all()]
    st_count = Student.objects.filter(current_class=c).count()
    print(f"Level {c.numeric_level:2d}: {c.name:20s} ({c.code:8s}) | Students: {st_count} | Sections: {secs}")
