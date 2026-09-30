import os
import django
from datetime import date
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from apps.accounts.models import User
from apps.teachers.models import Teacher, SalaryPayment

sample_non_teaching = [
    {
        'username': 'tariq.accounts',
        'first_name': 'Tariq',
        'last_name': 'Mehmood',
        'email': 'tariq.accounts@genxvision.edu.pk',
        'employee_id': 'STAFF-2026-001',
        'staff_type': Teacher.StaffType.NON_TEACHING,
        'designation': Teacher.Designation.ACCOUNTANT,
        'department': 'Accounts & Finance',
        'qualification': 'M.Com / MBA Finance',
        'experience_years': 6,
        'joining_date': date(2023, 1, 15),
        'basic_salary': Decimal('55000.00'),
        'phone_number': '+92 301 9988776',
        'residential_address': 'Flat 4B, Executive Complex, Islamabad',
        'status': Teacher.Status.ACTIVE
    },
    {
        'username': 'sadia.admin',
        'first_name': 'Sadia',
        'last_name': 'Rehman',
        'email': 'sadia.admin@genxvision.edu.pk',
        'employee_id': 'STAFF-2026-002',
        'staff_type': Teacher.StaffType.NON_TEACHING,
        'designation': Teacher.Designation.RECEPTIONIST,
        'department': 'Administration & Front Desk',
        'qualification': 'B.A / Computer Office Management',
        'experience_years': 4,
        'joining_date': date(2024, 3, 1),
        'basic_salary': Decimal('38000.00'),
        'phone_number': '+92 302 4455667',
        'residential_address': 'House 12, Street 5, G-11/3, Islamabad',
        'status': Teacher.Status.ACTIVE
    },
    {
        'username': 'imran.security',
        'first_name': 'Imran',
        'last_name': 'Khan',
        'email': 'imran.guard@genxvision.edu.pk',
        'employee_id': 'STAFF-2026-003',
        'staff_type': Teacher.StaffType.NON_TEACHING,
        'designation': Teacher.Designation.SECURITY_GUARD,
        'department': 'Security & Gatekeeping',
        'qualification': 'Matric / Ex-Serviceman',
        'experience_years': 8,
        'joining_date': date(2022, 6, 10),
        'basic_salary': Decimal('32000.00'),
        'phone_number': '+92 303 7788990',
        'residential_address': 'Staff Quarters #2, Campus Premises',
        'status': Teacher.Status.ACTIVE
    },
    {
        'username': 'rashid.driver',
        'first_name': 'Rashid',
        'last_name': 'Ali',
        'email': 'rashid.transport@genxvision.edu.pk',
        'employee_id': 'STAFF-2026-004',
        'staff_type': Teacher.StaffType.NON_TEACHING,
        'designation': Teacher.Designation.DRIVER,
        'department': 'Transport & Fleet',
        'qualification': 'Matric / HTV License Holder',
        'experience_years': 10,
        'joining_date': date(2021, 9, 1),
        'basic_salary': Decimal('35000.00'),
        'phone_number': '+92 304 3322110',
        'residential_address': 'House 90, Sector I-9, Islamabad',
        'status': Teacher.Status.ACTIVE
    },
]

for s in sample_non_teaching:
    user, _ = User.objects.get_or_create(
        username=s['username'],
        defaults={'email': s['email'], 'first_name': s['first_name'], 'last_name': s['last_name'], 'role': User.Role.COORDINATOR}
    )
    user.set_password('staff123')
    user.save()

    t, created = Teacher.objects.get_or_create(
        employee_id=s['employee_id'],
        defaults={
            'user': user,
            'staff_type': s['staff_type'],
            'designation': s['designation'],
            'department': s['department'],
            'qualification': s['qualification'],
            'experience_years': s['experience_years'],
            'joining_date': s['joining_date'],
            'basic_salary': s['basic_salary'],
            'phone_number': s['phone_number'],
            'residential_address': s['residential_address'],
            'status': s['status']
        }
    )
    if not created:
        t.staff_type = s['staff_type']
        t.designation = s['designation']
        t.department = s['department']
        t.basic_salary = s['basic_salary']
        t.save()
    print(f"Non-Teaching Staff: {t.get_full_name()} ({t.get_designation_display()}, {t.department})")

print("\n--- STAFF BREAKDOWN ---")
print("Total Staff:", Teacher.objects.count())
print("Teaching Faculty:", Teacher.objects.filter(staff_type=Teacher.StaffType.TEACHING).count())
print("Non-Teaching Staff:", Teacher.objects.filter(staff_type=Teacher.StaffType.NON_TEACHING).count())
