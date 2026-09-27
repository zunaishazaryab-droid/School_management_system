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

    def __str__(self):
        return f"{self.date} - {self.teacher.get_full_name()}: {self.get_status_display()}"
