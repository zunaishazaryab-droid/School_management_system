import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.academics.models import Subject, ClassRoom, Section, ClassSubject
from apps.accounts.models import User

teacher = User.objects.filter(role=User.Role.TEACHER).first()
if not teacher:
    teacher = User.objects.filter(role=User.Role.ADMIN).first()

new_subjects = [
    {
        'name': 'English A',
        'code': 'ENG-A',
        'total_marks': 100,
        'passing_marks': 33,
        'is_elective': False,
        'description': 'English Text, Reading & Literature'
    },
    {
        'name': 'English B',
        'code': 'ENG-B',
        'total_marks': 100,
        'passing_marks': 33,
        'is_elective': False,
        'description': 'English Grammar, Composition & Writing Skills'
    },
    {
        'name': 'Urdu A',
        'code': 'URD-A',
        'total_marks': 100,
        'passing_marks': 33,
        'is_elective': False,
        'description': 'Urdu Literature, Nazm-o-Nasr & Sabaq'
    },
    {
        'name': 'Urdu B',
        'code': 'URD-B',
        'total_marks': 100,
        'passing_marks': 33,
        'is_elective': False,
        'description': 'Urdu Qawaid-o-Insha, Mazmoon & Khatoot'
    },
]

created_subjects = []
for s_data in new_subjects:
    sub, created = Subject.objects.get_or_create(
        code=s_data['code'],
        defaults=s_data
    )
    if not created:
        sub.name = s_data['name']
        sub.total_marks = s_data['total_marks']
        sub.passing_marks = s_data['passing_marks']
        sub.description = s_data['description']
        sub.save()
    created_subjects.append(sub)
    print(f"{'Created' if created else 'Updated'} Subject: {sub.name} ({sub.code})")

# Assign new subjects to all ClassRooms and Sections
for cl in ClassRoom.objects.all():
    for sub in created_subjects:
        ClassSubject.objects.get_or_create(
            class_room=cl,
            subject=sub,
            defaults={'teacher': teacher}
        )
        for sec in cl.sections.all():
            ClassSubject.objects.get_or_create(
                class_room=cl,
                section=sec,
                subject=sub,
                defaults={'teacher': teacher}
            )

print("\n--- ALL CURRENT SUBJECTS IN DATABASE ---")
for s in Subject.objects.all().order_by('name'):
    print(f"  • {s.name} ({s.code}) - Total: {s.total_marks}, Passing: {s.passing_marks}")
