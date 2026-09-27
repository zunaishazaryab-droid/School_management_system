from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject
from apps.students.models import Student


class GradeScale(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. A+, A, B, C, D, E, F")
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g. 90.00")
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="e.g. 100.00")
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'), help_text="e.g. 4.00")
    remarks = models.CharField(max_length=100, default='Pass', help_text="e.g. Outstanding / Distinction, Excellent, Good, Pass, Fail")

    class Meta:
        ordering = ['-min_percentage']
        verbose_name = 'Grading Scale'
        verbose_name_plural = 'Grading Scales'

    def __str__(self):
        return f"Grade {self.name} ({self.min_percentage}% - {self.max_percentage}%) - {self.remarks}"

    @classmethod
    def get_grade_for_percentage(cls, percentage):
        pct = Decimal(str(percentage))
        grade = cls.objects.filter(min_percentage__lte=pct, max_percentage__gte=pct).first()
        if grade:
            return grade.name, grade.remarks
        if pct >= 90:
            return 'A+', 'Outstanding'
        elif pct >= 80:
            return 'A', 'Excellent'
        elif pct >= 70:
            return 'B', 'Very Good'
        elif pct >= 60:
            return 'C', 'Good'
        elif pct >= 50:
            return 'D', 'Satisfactory'
        elif pct >= 40:
            return 'E', 'Pass'
        else:
            return 'F', 'Needs Improvement'


class Exam(models.Model):
    class ExamType(models.TextChoices):
        MONTHLY_TEST = 'MONTHLY_TEST', 'Monthly Assessment'
        FIRST_TERM = 'FIRST_TERM', 'First Term Examination'
        MID_TERM = 'MID_TERM', 'Mid-Term Examination'
        FINAL_TERM = 'FINAL_TERM', 'Final Annual Examination'
        QUIZ_UNIT = 'QUIZ_UNIT', 'Quiz / Unit Test'

    title = models.CharField(max_length=150, help_text="e.g. Mid-Term Examination 2026, Annual Exam 2027")
    exam_type = models.CharField(max_length=30, choices=ExamType.choices, default=ExamType.MID_TERM)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='exams')
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=False, help_text="Publish result cards to parents & students")
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Examination'
        verbose_name_plural = 'Examinations'

    def __str__(self):
        return f"{self.title} ({self.academic_year.name})"


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='exam_schedules')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='exam_schedules')
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=33)
    room_number = models.CharField(max_length=50, blank=True, default='')

    class Meta:
        ordering = ['exam_date', 'start_time']
        unique_together = ('exam', 'class_room', 'subject')
        verbose_name = 'Exam Schedule / Date Sheet'
        verbose_name_plural = 'Exam Schedules / Date Sheets'

    def __str__(self):
        return f"{self.exam.title} - {self.class_room.name}: {self.subject.name} ({self.exam_date})"


class ExamMarks(models.Model):
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='marks_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=150, blank=True, default='')
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('exam_schedule', 'student')
        verbose_name = 'Exam Mark Record'
        verbose_name_plural = 'Exam Mark Records'

    def __str__(self):
        status = "ABSENT" if self.is_absent else f"{self.marks_obtained}/{self.exam_schedule.total_marks}"
        return f"{self.student.get_full_name()} - {self.exam_schedule.subject.name}: {status}"

    @property
    def percentage(self):
        if self.is_absent or self.exam_schedule.total_marks == 0:
            return Decimal('0.00')
        return (self.marks_obtained / Decimal(str(self.exam_schedule.total_marks))) * Decimal('100.00')


class ExamStudentResult(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='student_results')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='exam_results')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='class_exam_results')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='section_exam_results')
    
    total_marks = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    obtained_marks = models.DecimalField(max_digits=7, decimal_places=2, default=Decimal('0.00'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    grade = models.CharField(max_length=10, default='F')
    grade_remarks = models.CharField(max_length=100, default='Pass')
    position_in_section = models.PositiveIntegerField(null=True, blank=True)
    position_in_class = models.PositiveIntegerField(null=True, blank=True)
    is_passed = models.BooleanField(default=True)
    remarks = models.TextField(blank=True, default='')
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['class_room', 'section', 'position_in_section', '-percentage']
        unique_together = ('exam', 'student')
        verbose_name = 'Student Exam Result / Report Card'
        verbose_name_plural = 'Student Exam Results / Report Cards'

    def __str__(self):
        return f"{self.student.get_full_name()} ({self.exam.title}) - {self.percentage}% [{self.grade}]"
