from django.core.management.base import BaseCommand
from apps.accounts.models import User
from apps.core.models import SchoolSetting, Notification, ActivityLog


class Command(BaseCommand):
    help = 'Seeds initial users for all 4 roles (Admin, Principal, Coordinator, Teacher) and default school settings.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("Initializing Sprint 0 Database Seed..."))

        # 1. School Settings
        school_setting = SchoolSetting.get_settings()
        school_setting.school_name = "GEN'X VISION SCHOOL SYSTEM"
        school_setting.tagline = "Knowledge • Excellence • Leadership"
        school_setting.phone = "+92 300 9876543"
        school_setting.email = "admin@genxvision.edu.pk"
        school_setting.address = "Plot 42, Sector H-11, Education Complex"
        school_setting.current_academic_session = "2026-2027"
        school_setting.currency_symbol = "Rs."
        school_setting.save()
        self.stdout.write(self.style.SUCCESS("[OK] School settings configured."))

        # 2. Roles & Demo Accounts
        accounts = [
            {
                'username': 'admin',
                'email': 'admin@beaconheights.edu.pk',
                'password': 'admin123',
                'first_name': 'Muhammad',
                'last_name': 'Tariq (Owner/Admin)',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'phone_number': '+92 300 1112233',
                'bio': 'System Administrator & School Owner with full administrative privileges.'
            },
            {
                'username': 'principal',
                'email': 'principal@beaconheights.edu.pk',
                'password': 'principal123',
                'first_name': 'Dr. Asim',
                'last_name': 'Munir',
                'role': User.Role.PRINCIPAL,
                'is_staff': True,
                'is_superuser': False,
                'phone_number': '+92 300 2223344',
                'bio': 'School Principal overseeing academic excellence, faculty management, and student welfare.'
            },
            {
                'username': 'coordinator',
                'email': 'coordinator@beaconheights.edu.pk',
                'password': 'coordinator123',
                'first_name': 'Fatima',
                'last_name': 'Zahra',
                'role': User.Role.COORDINATOR,
                'is_staff': False,
                'is_superuser': False,
                'phone_number': '+92 300 3334455',
                'bio': 'Academic Coordinator managing syllabi, class schedules, timetable, and teacher reviews.'
            },
            {
                'username': 'teacher',
                'email': 'teacher@beaconheights.edu.pk',
                'password': 'teacher123',
                'first_name': 'Ahmed',
                'last_name': 'Bilal',
                'role': User.Role.TEACHER,
                'is_staff': False,
                'is_superuser': False,
                'phone_number': '+92 300 4445566',
                'bio': 'Senior Science & Mathematics Teacher for Classes 8, 9 and 10.'
            },
            {
                'username': 'student',
                'email': 'student@beaconheights.edu.pk',
                'password': 'student123',
                'first_name': 'Ali',
                'last_name': 'Hassan',
                'role': User.Role.STUDENT,
                'is_staff': False,
                'is_superuser': False,
                'phone_number': '+92 300 5556677',
                'bio': 'Active enrolled student account for dedicated Student Portal.'
            }
        ]

        for acc in accounts:
            user, created = User.objects.get_or_create(username=acc['username'])
            user.email = acc['email']
            user.first_name = acc['first_name']
            user.last_name = acc['last_name']
            user.role = acc['role']
            user.is_staff = acc['is_staff']
            user.is_superuser = acc['is_superuser']
            user.phone_number = acc['phone_number']
            user.bio = acc['bio']
            user.set_password(acc['password'])
            user.save()
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"[OK] {action} user: {user.username} ({user.get_role_display()})"))

        # Link student user to first active student record
        from apps.students.models import Student
        first_student = Student.objects.filter(status='ACTIVE').first() or Student.objects.first()
        student_user = User.objects.filter(username='student').first()
        if first_student and student_user:
            student_user.first_name = first_student.first_name
            student_user.last_name = first_student.last_name
            student_user.save(update_fields=['first_name', 'last_name'])
            first_student.user = student_user
            first_student.save(update_fields=['user'])
            self.stdout.write(self.style.SUCCESS(f"[OK] Linked student user '{student_user.username}' ({student_user.get_full_name()}) to student record '{first_student.get_full_name()}' ({first_student.admission_number})."))

        # 3. Seed Sample Notifications
        Notification.objects.all().delete()
        admin_user = User.objects.get(username='admin')
        
        Notification.objects.create(
            title="System Initialized Successfully",
            message="Sprint 0 Foundation is active. Roles, base theme, and security configured.",
            notification_type=Notification.NotificationType.SUCCESS,
            link=""
        )
        Notification.objects.create(
            title="Academic Session 2026-2027 Active",
            message="Please review class capacities and teacher assignments before next term.",
            notification_type=Notification.NotificationType.INFO,
            link=""
        )
        Notification.objects.create(
            title="Monthly Fee Reconciliation Reminder",
            message="Monthly fee cycle closing in 5 days. Ensure all pending slips are accounted for.",
            notification_type=Notification.NotificationType.WARNING,
            link=""
        )
        self.stdout.write(self.style.SUCCESS("[OK] Seeded sample notifications."))

        # 4. Initial Activity Log
        ActivityLog.objects.create(
            user=admin_user,
            action='INITIALIZE',
            module='Core',
            description='Sprint 0 foundation and database seeded successfully.',
            ip_address='127.0.0.1'
        )
        self.stdout.write(self.style.SUCCESS("[OK] Activity log initialized."))
        self.stdout.write(self.style.SUCCESS("\n[SUCCESS] Sprint 0 Seed completed successfully!"))
