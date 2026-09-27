from django.db import models
from django.conf import settings


class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. 2026-2027")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False, help_text="Mark if this is the active academic session")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} {'(Active)' if self.is_current else ''}"

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)


class ClassRoom(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Nursery, Prep, Class 1, Class 10")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. NUR, PREP, C1, C10")
    numeric_level = models.IntegerField(default=1, help_text="Numeric order for promotions (e.g. 1 for Class 1)")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['numeric_level', 'name']
        verbose_name = 'Class'
        verbose_name_plural = 'Classes'

    def __str__(self):
        return self.name

    @property
    def total_students_count(self):
        return self.students.filter(status='ACTIVE').count()


class Section(models.Model):
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=50, help_text="e.g. A, B, Blue, Green")
    capacity = models.PositiveIntegerField(default=40)
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_sections'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['class_room__numeric_level', 'name']
        unique_together = ('class_room', 'name')

    def __str__(self):
        return f"{self.class_room.name} - Section {self.name}"

    @property
    def enrolled_students_count(self):
        return self.students.filter(status='ACTIVE').count()


class Subject(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, unique=True, help_text="e.g. MATH-01, ENG-01")
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=33)
    is_elective = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class ClassSubject(models.Model):
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='class_subjects')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, related_name='section_subjects')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='assigned_classes')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teaching_subjects'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('class_room', 'section', 'subject')
        verbose_name = 'Subject Assignment'
        verbose_name_plural = 'Subject Assignments'

    def __str__(self):
        sec_str = f" - Sec {self.section.name}" if self.section else ""
        return f"{self.class_room.name}{sec_str} : {self.subject.name}"


class Period(models.Model):
    name = models.CharField(max_length=50, help_text="e.g. Period 1, Period 2, Recess / Break, Period 5")
    period_number = models.PositiveIntegerField(default=1)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_break = models.BooleanField(default=False, help_text="Mark if this period is recess / lunch break")

    class Meta:
        ordering = ['period_number', 'start_time']
        verbose_name = 'Timetable Period'
        verbose_name_plural = 'Timetable Periods'

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')})"


class TimetableEntry(models.Model):
    class DayOfWeek(models.TextChoices):
        MONDAY = 'MONDAY', 'Monday'
        TUESDAY = 'TUESDAY', 'Tuesday'
        WEDNESDAY = 'WEDNESDAY', 'Wednesday'
        THURSDAY = 'THURSDAY', 'Thursday'
        FRIDAY = 'FRIDAY', 'Friday'
        SATURDAY = 'SATURDAY', 'Saturday'

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='timetable_entries')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='timetable_entries')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetable_entries')
    day_of_week = models.CharField(max_length=20, choices=DayOfWeek.choices, default=DayOfWeek.MONDAY)
    period = models.ForeignKey(Period, on_delete=models.CASCADE, related_name='timetable_entries')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='timetable_entries')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='timetable_slots'
    )
    room_number = models.CharField(max_length=50, blank=True, default='', help_text="e.g. Room 104 / Science Lab")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['day_of_week', 'period__period_number']
        unique_together = ('academic_year', 'class_room', 'section', 'day_of_week', 'period')
        verbose_name = 'Timetable Slot'
        verbose_name_plural = 'Timetable Slots'

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.period.name}: {self.class_room.name} ({self.section.name}) - {self.subject.name}"
