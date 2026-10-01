import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.students.models import Student
from apps.students.views import get_or_create_student_user

students = Student.objects.all()
print(f"Total students found: {students.count()}")

for st in students:
    user = get_or_create_student_user(st)
    print(f"Linked Student: {st.get_full_name()} ({st.admission_number}) -> Username: '{user.username}', Role: '{user.role}'")

print("\nAll students have been synchronized with student portal accounts!")
