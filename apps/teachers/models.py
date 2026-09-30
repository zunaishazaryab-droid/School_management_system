from django.db import models
from django.conf import settings
from decimal import Decimal


class Teacher(models.Model):
    class StaffType(models.TextChoices):
        TEACHING = 'TEACHING', 'Teaching Faculty'
        NON_TEACHING = 'NON_TEACHING', 'Non-Teaching Staff'

    class Designation(models.TextChoices):
        # Teaching Designations
        SENIOR_TEACHER = 'SENIOR_TEACHER', 'Senior Teacher'
        JUNIOR_TEACHER = 'JUNIOR_TEACHER', 'Junior Teacher'
        SUBJECT_SPECIALIST = 'SUBJECT_SPECIALIST', 'Subject Specialist'
        PRIMARY_TEACHER = 'PRIMARY_TEACHER', 'Primary School Teacher'
        SPORTS_INSTRUCTOR = 'SPORTS_INSTRUCTOR', 'Sports / Physical Instructor'
        LAB_INSTRUCTOR = 'LAB_INSTRUCTOR', 'Lab Incharge / Science Instructor'

        # Non-Teaching Designations
        ACCOUNTANT = 'ACCOUNTANT', 'Accountant / Finance Officer'
        ADMIN_OFFICER = 'ADMIN_OFFICER', 'Administrative Officer / Clerk'
        LIBRARIAN = 'LIBRARIAN', 'Librarian'
        IT_SUPPORT = 'IT_SUPPORT', 'IT Support / Computer Operator'
        RECEPTIONIST = 'RECEPTIONIST', 'Receptionist / Front Desk'
        SECURITY_GUARD = 'SECURITY_GUARD', 'Security Guard'
        DRIVER = 'DRIVER', 'Transport Driver'
        SUPPORT_STAFF = 'SUPPORT_STAFF', 'Aayah / Peon / Support Staff'
        MAINTENANCE = 'MAINTENANCE', 'Electrician / Maintenance Staff'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'
        RESIGNED = 'RESIGNED', 'Resigned'
        TERMINATED = 'TERMINATED', 'Terminated'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        help_text="Login user account for this teacher/staff"
    )
    employee_id = models.CharField(max_length=50, unique=True, help_text="e.g. EMP-2026-001")
    staff_type = models.CharField(
        max_length=20,
        choices=StaffType.choices,
        default=StaffType.TEACHING,
        help_text="Classification: Teaching Faculty or Non-Teaching Staff"
    )
    designation = models.CharField(max_length=50, choices=Designation.choices, default=Designation.SUBJECT_SPECIALIST)
    department = models.CharField(max_length=100, default='Academics', blank=True)
    qualification = models.CharField(max_length=150, help_text="e.g. M.Sc Mathematics, B.Ed, M.Phil")
    experience_years = models.PositiveIntegerField(default=2, help_text="Total years of teaching experience")
    joining_date = models.DateField()
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('45000.00'))
    
    # Personal & Contact
    cnic = models.CharField(max_length=30, blank=True, null=True, help_text="National Identity Card Number")
    phone_number = models.CharField(max_length=30, help_text="Primary WhatsApp / Mobile Number")
    emergency_contact = models.CharField(max_length=30, blank=True, null=True)
    residential_address = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    photo = models.ImageField(upload_to='teacher_photos/', blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['employee_id', 'user__first_name']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name() or self.user.username} ({self.get_designation_display()})"

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username


class SalaryPayment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        CHEQUE = 'CHEQUE', 'Cheque'

    class Status(models.TextChoices):
        PAID = 'PAID', 'Paid'
        PENDING = 'PENDING', 'Pending'

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='salary_payments')
    salary_month = models.CharField(max_length=20, help_text="e.g. April 2026")
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(blank=True, null=True)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.BANK_TRANSFER)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.salary_month} ({self.status})"

    def save(self, *args, **kwargs):
        self.net_salary = self.basic_salary + self.allowances - self.deductions
        super().save(*args, **kwargs)


class StaffLeave(models.Model):
    class LeaveType(models.TextChoices):
        CASUAL = 'CASUAL', 'Casual Leave'
        MEDICAL = 'MEDICAL', 'Medical / Sick Leave'
        ANNUAL = 'ANNUAL', 'Annual / Earned Leave'
        UNPAID = 'UNPAID', 'Unpaid Leave'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.CharField(max_length=20, choices=LeaveType.choices, default=LeaveType.CASUAL)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.get_leave_type_display()} ({self.status})"


class TeacherPerformance(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='performance_evaluations')
    evaluation_month = models.CharField(max_length=30, help_text="e.g. April 2026")
    punctuality_rating = models.PositiveIntegerField(default=95, help_text="Percentage out of 100")
    syllabus_coverage_pct = models.PositiveIntegerField(default=90, help_text="Percentage of allocated topics completed")
    homework_regularity_pct = models.PositiveIntegerField(default=92, help_text="Percentage")
    copies_checked_pct = models.PositiveIntegerField(default=95, help_text="Percentage of notebooks checked")
    coordinator_remarks = models.TextField(blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('9.2'))
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher.get_full_name()} - {self.evaluation_month} (Score: {self.overall_score}/10)"
