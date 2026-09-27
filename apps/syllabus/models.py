from django.db import models
from django.conf import settings
from apps.academics.models import ClassRoom, Subject, AcademicYear


class SyllabusChapter(models.Model):
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='syllabus_chapters')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='syllabus_chapters')
    chapter_number = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200, help_text="e.g. Chapter 1: Quadratic Equations")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['class_room__numeric_level', 'subject__name', 'chapter_number']
        unique_together = ('class_room', 'subject', 'chapter_number')

    def __str__(self):
        return f"{self.class_room.name} - {self.subject.name}: Ch {self.chapter_number}. {self.title}"

    @property
    def total_topics_count(self):
        return self.topics.count()

    @property
    def completed_topics_count(self):
        return self.topics.filter(status=SyllabusTopic.Status.COMPLETED).count()

    @property
    def progress_pct(self):
        total = self.total_topics_count
        if total == 0:
            return 0
        return int((self.completed_topics_count / total) * 100)


class SyllabusTopic(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = 'NOT_STARTED', 'Not Started'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'

    chapter = models.ForeignKey(SyllabusChapter, on_delete=models.CASCADE, related_name='topics')
    topic_number = models.CharField(max_length=20, default='1.1', help_text="e.g. 1.1, 1.2")
    title = models.CharField(max_length=255, help_text="e.g. Derivation of Quadratic Formula")
    estimated_periods = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    completion_date = models.DateField(blank=True, null=True)
    teacher_notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['chapter', 'topic_number']

    def __str__(self):
        return f"{self.topic_number} {self.title} ({self.get_status_display()})"
