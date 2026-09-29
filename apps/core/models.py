from django.db import models
from django.conf import settings


class SchoolSetting(models.Model):
    school_name = models.CharField(max_length=200, default='Elite Model School')
    tagline = models.CharField(max_length=255, default='Knowledge, Excellence & Integrity', blank=True)
    logo = models.ImageField(upload_to='school_branding/', blank=True, null=True)
    phone = models.CharField(max_length=30, default='+92 300 1234567', blank=True)
    email = models.EmailField(default='info@eliteschool.edu.pk', blank=True)
    address = models.TextField(default='Main Campus, Education City', blank=True)
    current_academic_session = models.CharField(max_length=50, default='2026-2027', blank=True)
    currency_symbol = models.CharField(max_length=10, default='Rs.', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'School Setting'
        verbose_name_plural = 'School Settings'

    def __str__(self):
        return self.school_name

    @classmethod
    def get_settings(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        INFO = 'INFO', 'Information'
        SUCCESS = 'SUCCESS', 'Success'
        WARNING = 'WARNING', 'Warning'
        DANGER = 'DANGER', 'Urgent / Danger'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Target user. Leave blank for broadcast to all staff."
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, default='')
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_notification_type_display()})"


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=50)  # e.g., LOGIN, LOGOUT, CREATE, UPDATE, DELETE
    module = models.CharField(max_length=100)  # e.g., Accounts, Students, Fees, Attendance
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.username if self.user else 'System'
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {username} - {self.action} ({self.module})"

    @classmethod
    def log_activity(cls, user, action, module, description, ip_address=None):
        try:
            return cls.objects.create(
                user=user if getattr(user, 'is_authenticated', False) else None,
                action=action,
                module=module,
                description=description,
                ip_address=ip_address
            )
        except Exception:
            pass


class Branch(models.Model):
    class CampusType(models.TextChoices):
        MAIN = 'MAIN', 'Main / Principal Campus'
        JUNIOR = 'JUNIOR', 'Junior / Primary Wing'
        GIRLS = 'GIRLS', 'Girls Wing'
        BOYS = 'BOYS', 'Boys Wing'
        CITY = 'CITY', 'City Branch'

    name = models.CharField(max_length=150, help_text="e.g. Main Campus Johar Town")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. GXV-MC01")
    campus_type = models.CharField(max_length=20, choices=CampusType.choices, default=CampusType.MAIN)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, default="Lahore")
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    principal_name = models.CharField(max_length=120, blank=True)
    is_main_branch = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_main_branch', 'name']
        verbose_name = 'Campus / Branch'
        verbose_name_plural = 'Campuses & Branches'

    def __str__(self):
        return f"{self.name} ({self.code})"

