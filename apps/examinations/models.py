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
        WEEKLY_TEST = 'WEEKLY_TEST', 'Weekly Test'
        MONTHLY_TEST = 'MONTHLY_TEST', 'Monthly Assessment'
        FIRST_TERM = 'FIRST_TERM', 'First Term Examination'
        SECOND_TERM = 'SECOND_TERM', 'Second Term Examination'
        MID_TERM = 'MID_TERM', 'Mid-Term Examination'
        FINAL_TERM = 'FINAL_TERM', 'Final Annual Examination'
        QUIZ_UNIT = 'QUIZ_UNIT', 'Class / Unit Test'

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


class OnlineAssessment(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PUBLISHED = 'PUBLISHED', 'Published / Live'
        CLOSED = 'CLOSED', 'Closed / Archived'

    title = models.CharField(max_length=200, help_text="e.g. Physics Chapter 4 Motion Online CBT Quiz")
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='online_quizzes')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='online_quizzes')
    duration_minutes = models.PositiveIntegerField(default=30, help_text="Total test time in minutes")
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))
    passing_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('40.00'))
    start_window = models.DateTimeField(null=True, blank=True)
    end_window = models.DateTimeField(null=True, blank=True)
    shuffle_questions = models.BooleanField(default=True)
    show_instant_result = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PUBLISHED)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Online Assessment / CBT Quiz'
        verbose_name_plural = 'Online Assessments & CBT Quizzes'

    def __str__(self):
        return f"{self.title} ({self.class_room.name} - {self.subject.name})"


class AssessmentQuestion(models.Model):
    class QuestionType(models.TextChoices):
        MCQ = 'MCQ', 'Multiple Choice Question (4 Options)'
        TRUE_FALSE = 'TRUE_FALSE', 'True / False'

    assessment = models.ForeignKey(OnlineAssessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QuestionType.choices, default=QuestionType.MCQ)
    option_a = models.CharField(max_length=255, default='')
    option_b = models.CharField(max_length=255, default='')
    option_c = models.CharField(max_length=255, blank=True, default='')
    option_d = models.CharField(max_length=255, blank=True, default='')
    correct_answer = models.CharField(max_length=10, help_text="A, B, C, D, TRUE, or FALSE")
    marks = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('2.00'))
    explanation = models.TextField(blank=True, help_text="Solution or reference explanation")
    order_num = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order_num', 'id']
        verbose_name = 'Assessment Question'
        verbose_name_plural = 'Assessment Questions'

    def __str__(self):
        return f"Q#{self.order_num}: {self.question_text[:50]}"


class StudentAssessmentAttempt(models.Model):
    assessment = models.ForeignKey(OnlineAssessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score_obtained = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    is_passed = models.BooleanField(default=False)
    answers_payload = models.JSONField(default=dict, blank=True)
    time_taken_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-submitted_at']
        unique_together = ('assessment', 'student')
        verbose_name = 'Student CBT Attempt'
        verbose_name_plural = 'Student CBT Attempts'

    def __str__(self):
        return f"{self.student.get_full_name()} on {self.assessment.title}: {self.score_obtained}/{self.assessment.total_marks} ({self.percentage}%)"

