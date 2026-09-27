from django.db import models
from django.conf import settings
from apps.academics.models import ClassRoom, Section, Subject


class DailyLecture(models.Model):
    date = models.DateField(db_index=True)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='lecture_logs')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='lecture_logs')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='lecture_logs')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conducted_lectures'
    )
    chapter_name = models.CharField(max_length=200, help_text="Chapter / Unit Title")
    topic = models.CharField(max_length=255, help_text="Specific topic covered today")
    learning_objectives = models.TextField(blank=True, help_text="Key concepts taught")
    classwork_description = models.TextField(help_text="Exercises, formulas, or questions solved in class")
    homework_assigned = models.TextField(blank=True, help_text="Homework task given to students")
    present_students_count = models.PositiveIntegerField(default=0)
    absent_students_count = models.PositiveIntegerField(default=0)
    copies_checked_count = models.PositiveIntegerField(default=0, help_text="Number of student notebooks checked")
    remarks = models.TextField(blank=True, help_text="Student discipline, pacing, or coordinator feedback")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Daily Lecture Record'
        verbose_name_plural = 'Daily Lecture Records'

    def __str__(self):
        return f"{self.date} - {self.class_room.name} ({self.subject.name}): {self.topic}"


class Homework(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active / In-Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted & Checked'
        ARCHIVED = 'ARCHIVED', 'Archived'

    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='homework_assignments')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='homework_assignments')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='homework_assignments')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assigned_homeworks'
    )
    title = models.CharField(max_length=200, help_text="e.g. Exercise 4.2 Questions 1 to 5")
    description = models.TextField(help_text="Detailed instructions or reference pages")
    assigned_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    attachment = models.FileField(upload_to='homework_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-assigned_date', '-created_at']
        verbose_name = 'Homework / Class Diary'
        verbose_name_plural = 'Homework & Diary Records'

    def __str__(self):
        return f"{self.title} - {self.class_room.name} ({self.subject.name})"
