from django.db import models
from django.conf import settings
from apps.academics.models import ClassRoom, Section, AcademicYear


class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        GRADUATED = 'GRADUATED', 'Graduated'
        TRANSFERRED = 'TRANSFERRED', 'Transferred'
        EXPELLED = 'EXPELLED', 'Expelled'

    # User Account for Student Portal
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
        help_text="Linked user login account for dedicated Student Portal"
    )

    # Academic & ID Information
    admission_number = models.CharField(max_length=50, unique=True, help_text="Unique Student / Admission ID (e.g. STU-2026-001)")
    roll_number = models.CharField(max_length=30, blank=True, null=True, help_text="Class Roll Number")
    current_class = models.ForeignKey(ClassRoom, on_delete=models.PROTECT, related_name='students')
    current_section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name='students')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='enrolled_students')
    admission_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    date_of_birth = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True, help_text="e.g. A+, B+, O+, AB-")
    religion = models.CharField(max_length=50, default='Islam', blank=True)
    nationality = models.CharField(max_length=50, default='Pakistani', blank=True)
    
    # Guardian / Contact Information
    guardian_name = models.CharField(max_length=150)
    guardian_relationship = models.CharField(max_length=50, default='Father', help_text="e.g. Father, Mother, Uncle, Guardian")
    guardian_cnic = models.CharField(max_length=30, blank=True, null=True, help_text="National ID / B-Form Number")
    guardian_phone = models.CharField(max_length=30, help_text="Primary WhatsApp / Phone Number")
    emergency_contact = models.CharField(max_length=30, blank=True, null=True)
    guardian_email = models.EmailField(blank=True, null=True)
    guardian_occupation = models.CharField(max_length=100, blank=True, null=True)
    residential_address = models.TextField()
    city = models.CharField(max_length=80, default='Islamabad', blank=True)

    # Health & Previous History
    previous_school = models.CharField(max_length=200, blank=True, null=True)
    medical_notes = models.TextField(blank=True, null=True, help_text="Allergies, chronic conditions, emergency notes")
    
    # Media & Reserved Hardware Fields
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    biometric_id = models.CharField(max_length=100, blank=True, null=True, help_text="Reserved for future Biometric Attendance hardware integration")

    # Meta timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['current_class__numeric_level', 'current_section__name', 'roll_number', 'first_name']

    def __str__(self):
        return f"{self.admission_number} - {self.get_full_name()} ({self.current_class.name})"

    def get_full_name(self):
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


class StudentDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=150, help_text="e.g. B-Form, Birth Certificate, Previous School Leaving Certificate")
    document_file = models.FileField(upload_to='student_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.title}"


class StudentPromotionHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='promotion_history')
    from_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, related_name='promoted_from_records')
    from_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, related_name='promoted_from_sections')
    to_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, related_name='promoted_to_records')
    to_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, related_name='promoted_to_sections')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.SET_NULL, null=True)
    promotion_date = models.DateField(auto_now_add=True)
    promoted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True, help_text="e.g. Promoted with Grade A on Annual Exam 2026")

    class Meta:
        ordering = ['-promotion_date']

    def __str__(self):
        return f"{self.student.get_full_name()}: {self.from_class} -> {self.to_class}"
