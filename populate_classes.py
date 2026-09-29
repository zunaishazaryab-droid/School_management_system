import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.academics.models import ClassRoom, Section
from apps.accounts.models import User

teacher = User.objects.filter(role=User.Role.TEACHER).first()

classes_to_add = [
    {'name': 'Class 3', 'code': 'C3', 'level': 5, 'sections': ['A', 'B']},
    {'name': 'Class 4', 'code': 'C4', 'level': 6, 'sections': ['A', 'B']},
    {'name': 'Class 6', 'code': 'C6', 'level': 8, 'sections': ['A', 'B']},
    {'name': 'Class 7', 'code': 'C7', 'level': 9, 'sections': ['A', 'B']},
    {'name': 'Class 8', 'code': 'C8', 'level': 10, 'sections': ['A', 'B']},
]

for c in classes_to_add:
    cls, created = ClassRoom.objects.get_or_create(
        code=c['code'],
        defaults={'name': c['name'], 'numeric_level': c['level'], 'description': f"Standard curriculum level for {c['name']}."}
    )
    if not created:
        cls.name = c['name']
        cls.numeric_level = c['level']
        cls.save()
    for s_name in c['sections']:
        Section.objects.get_or_create(
            class_room=cls,
            name=s_name,
            defaults={'capacity': 35, 'class_teacher': teacher}
        )

print("SUCCESS: Classes and sections added successfully!")
for cl in ClassRoom.objects.all().order_by('numeric_level'):
    secs = ", ".join([s.name for s in cl.sections.all()])
    print(f"Level {cl.numeric_level:2d}: {cl.name} ({cl.code}) -> Sections: [{secs}]")
