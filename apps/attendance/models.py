from django.db import models
from django.conf import settings
from apps.students.models import Student
from apps.academics.models import ClassRoom, Section
from apps.teachers.models import Teacher


class StudentAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        HALF_DAY = 'HALF_DAY', 'Half Day'
        EXCUSED = 'EXCUSED', 'Excused / Leave'

    date = models.DateField(db_index=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='student_attendance_records')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='student_attendance_records')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    remarks = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'student__roll_number', 'student__first_name']
        unique_together = ('date', 'student')
        verbose_name = 'Student Attendance'
        verbose_name_plural = 'Student Attendance Records'

    def __str__(self):
        return f"{self.date} - {self.student.get_full_name()}: {self.get_status_display()}"


class TeacherAttendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        HALF_DAY = 'HALF_DAY', 'Half Day'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'

    date = models.DateField(db_index=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    check_in_time = models.TimeField(blank=True, null=True)
    check_out_time = models.TimeField(blank=True, null=True)
    remarks = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', 'teacher__employee_id']
        unique_together = ('date', 'teacher')
        verbose_name = 'Teacher Attendance'
        verbose_name_plural = 'Teacher Attendance Records'

class BiometricDevice(models.Model):
    class Status(models.TextChoices):
        ONLINE = 'ONLINE', 'Online / Connected'
        OFFLINE = 'OFFLINE', 'Offline'
        SYNCING = 'SYNCING', 'Syncing'

    class DeviceType(models.TextChoices):
        FINGERPRINT = 'FINGERPRINT', 'Fingerprint Terminal'
        FACIAL = 'FACIAL', 'Facial Recognition'
        RFID = 'RFID', 'RFID / Card Reader'
        HYBRID = 'HYBRID', 'Hybrid (Face + Finger + Card)'

    name = models.CharField(max_length=120, help_text="e.g. Main Gate Terminal A")
    device_type = models.CharField(max_length=30, choices=DeviceType.choices, default=DeviceType.FINGERPRINT)
    ip_address = models.GenericIPAddressField(default="192.168.1.201")
    port = models.PositiveIntegerField(default=4370, help_text="Default ZKTeco / standalone port 4370")
    location = models.CharField(max_length=150, default="Main Entrance Gate")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ONLINE)
    is_active = models.BooleanField(default=True)
    last_sync_time = models.DateTimeField(null=True, blank=True)
    total_logs_synced = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Biometric Device'
        verbose_name_plural = 'Biometric Devices'

    def __str__(self):
        return f"{self.name} ({self.ip_address}:{self.port}) - {self.get_status_display()}"


class BiometricPunch(models.Model):
    class PunchType(models.TextChoices):
        CHECK_IN = 'CHECK_IN', 'Check In (Arrival)'
        CHECK_OUT = 'CHECK_OUT', 'Check Out (Departure)'

    device = models.ForeignKey(BiometricDevice, on_delete=models.CASCADE, related_name='punches')
    biometric_user_id = models.CharField(max_length=50, help_text="Enrollment ID stored on device")
    timestamp = models.DateTimeField(db_index=True)
    punch_type = models.CharField(max_length=20, choices=PunchType.choices, default=PunchType.CHECK_IN)
    is_processed = models.BooleanField(default=False)
    matched_student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='biometric_punches')
    matched_teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True, related_name='biometric_punches')
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Biometric Punch Log'
        verbose_name_plural = 'Biometric Punch Logs'

    def __str__(self):
        return f"User #{self.biometric_user_id} on {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.punch_type}"


class StudentLeaveRequest(models.Model):
    class Category(models.TextChoices):
        SICK = 'SICK', 'Medical / Sickness'
        CASUAL = 'CASUAL', 'Casual / Family Matter'
        EMERGENCY = 'EMERGENCY', 'Urgent Emergency'
        OFFICIAL = 'OFFICIAL', 'Sports / Official Event'
        OTHER = 'OTHER', 'Other Reason'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved (Excused)'
        REJECTED = 'REJECTED', 'Rejected'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.CASUAL)
    reason = models.TextField(help_text="Detailed reason for absence")
    document = models.FileField(upload_to='leave_documents/', null=True, blank=True, help_text="Doctor slip or letter")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    applied_by_name = models.CharField(max_length=120, blank=True, help_text="Guardian or Student name")
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_leave_requests'
    )
    admin_remarks = models.CharField(max_length=255, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']
        verbose_name = 'Student Leave Request'
        verbose_name_plural = 'Student Leave Requests'

    def __str__(self):
        return f"Leave #{self.id}: {self.student.get_full_name()} ({self.start_date} to {self.end_date}) - {self.get_status_display()}"
