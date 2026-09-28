from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.academics.models import ClassRoom, Section


class Announcement(models.Model):
    class Priority(models.TextChoices):
        NORMAL = 'NORMAL', 'Normal Notice'
        IMPORTANT = 'IMPORTANT', 'Important'
        URGENT = 'URGENT', 'Urgent / High Alert'

    class Audience(models.TextChoices):
        ALL = 'ALL', 'All School (Students, Staff, Parents)'
        STUDENTS = 'STUDENTS', 'Students & Parents'
        TEACHERS = 'TEACHERS', 'Faculty & Staff Only'
        CLASS_SPECIFIC = 'CLASS_SPECIFIC', 'Specific Class'

    title = models.CharField(max_length=200, help_text="e.g. Sports Day Schedule, Fee Submission Deadline")
    content = models.TextField(help_text="Detailed announcement content or circular description")
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)
    target_class = models.ForeignKey(ClassRoom, on_delete=models.SET_NULL, null=True, blank=True, related_name='class_announcements')
    target_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='section_announcements')
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True, help_text="Optional circular PDF or photo")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_announcements')
    is_published = models.BooleanField(default=True)
    publish_date = models.DateField(default=timezone.now)
    expiry_date = models.DateField(null=True, blank=True, help_text="Notice will hide automatically after this date")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-publish_date', '-created_at']
        verbose_name = 'Announcement & Circular'
        verbose_name_plural = 'Announcements & Circulars'

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"

    @property
    def is_active(self):
        if not self.is_published:
            return False
        today = timezone.now().date()
        if self.expiry_date and self.expiry_date < today:
            return False
        return self.publish_date <= today


class MessageTemplate(models.Model):
    class Category(models.TextChoices):
        ABSENCE = 'ABSENCE', 'Student Absence Alert'
        FEE_REMINDER = 'FEE_REMINDER', 'Fee Dues & Recovery Reminder'
        EXAM_ALERT = 'EXAM_ALERT', 'Exam Schedule & Date Sheet'
        HOMEWORK = 'HOMEWORK', 'Daily Homework / Diary'
        RESULT = 'RESULT', 'Exam Result Announcement'
        GENERAL = 'GENERAL', 'General Circular / Notice'

    title = models.CharField(max_length=150, help_text="e.g. Uninformed Absence Alert Template")
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.GENERAL)
    body = models.TextField(
        help_text="Message text. Available placeholders: {student_name}, {guardian_name}, {class_name}, {fee_month}, {due_amount}, {date}, {school_name}"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'title']
        verbose_name = 'Message Template'
        verbose_name_plural = 'Message Templates'

    def __str__(self):
        return f"{self.title} ({self.get_category_display()})"


class DirectMessageLog(models.Model):
    class RecipientType(models.TextChoices):
        STUDENT = 'STUDENT', 'Student / Parent'
        TEACHER = 'TEACHER', 'Teacher / Staff'
        CLASS = 'CLASS', 'Class Cohort'

    class Channel(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        SMS = 'SMS', 'SMS'

    class Status(models.TextChoices):
        SENT = 'SENT', 'Sent / Dispatched'
        DELIVERED = 'DELIVERED', 'Delivered'
        FAILED = 'FAILED', 'Failed'
        DRAFT = 'DRAFT', 'Prepared / Logged'

    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices, default=RecipientType.STUDENT)
    recipient_name = models.CharField(max_length=150)
    recipient_phone = models.CharField(max_length=30)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.WHATSAPP)
    template = models.ForeignKey(MessageTemplate, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_logs')
    message_body = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SENT)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Direct Message Log'
        verbose_name_plural = 'Direct Message Logs'


class SMSWhatsAppGateway(models.Model):
    class Provider(models.TextChoices):
        LOCAL_SIMULATOR = 'LOCAL_SIMULATOR', 'Local Simulator / Standard Log Engine'
        TWILIO = 'TWILIO', 'Twilio (SMS / WhatsApp)'
        INFOBIP = 'INFOBIP', 'Infobip Global Gateway'
        CUSTOM_WEBHOOK = 'CUSTOM_WEBHOOK', 'Custom HTTP Webhook / Local GSM Gateway'

    class ChannelType(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp Business API'
        SMS = 'SMS', 'SMS Gateway'
        HYBRID = 'HYBRID', 'Hybrid (WhatsApp + SMS Fallback)'

    name = models.CharField(max_length=120, help_text="e.g. GenX Vision WhatsApp Gateway")
    provider = models.CharField(max_length=30, choices=Provider.choices, default=Provider.LOCAL_SIMULATOR)
    channel_type = models.CharField(max_length=20, choices=ChannelType.choices, default=ChannelType.WHATSAPP)
    sender_id = models.CharField(max_length=50, default="GENX-VISION", help_text="Masking ID or WhatsApp Phone Number")
    api_endpoint = models.URLField(blank=True, default="http://127.0.0.1:8000/api/v1/mock-gateway/")
    api_key = models.CharField(max_length=255, blank=True, help_text="API Token / Auth Token")
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'SMS & WhatsApp Gateway'
        verbose_name_plural = 'SMS & WhatsApp Gateways'

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()}) - {'Active' if self.is_active else 'Inactive'}"


class AutomatedNotificationRule(models.Model):
    class TriggerEvent(models.TextChoices):
        DAILY_ABSENCE = 'DAILY_ABSENCE', 'Daily Student Uninformed Absence Alert'
        FEE_OVERDUE = 'FEE_OVERDUE', 'Monthly Fee Defaulter / Dues Reminder'
        EXAM_RESULT = 'EXAM_RESULT', 'Exam Result / Term Report Card Published'
        HOMEWORK_DAILY = 'HOMEWORK_DAILY', 'Daily Class Homework Diary Dispatched'
        LEAVE_APPROVED = 'LEAVE_APPROVED', 'Leave Request Approved / Status Update'

    class Channel(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp Only'
        SMS = 'SMS', 'SMS Only'
        BOTH = 'BOTH', 'Both WhatsApp & SMS'

    event_type = models.CharField(max_length=30, choices=TriggerEvent.choices, unique=True)
    template = models.ForeignKey(MessageTemplate, on_delete=models.CASCADE, related_name='auto_rules')
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.WHATSAPP)
    is_enabled = models.BooleanField(default=True)
    auto_trigger_time = models.TimeField(null=True, blank=True, help_text="Scheduled daily auto-run time (e.g. 10:00 AM)")
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Automated Notification Rule'
        verbose_name_plural = 'Automated Notification Rules'

    def __str__(self):
        return f"Auto-Trigger: {self.get_event_type_display()} ({'Enabled' if self.is_enabled else 'Disabled'})"


class NotificationQueue(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending in Queue'
        SENT = 'SENT', 'Sent / Dispatched'
        DELIVERED = 'DELIVERED', 'Delivered to Recipient'
        FAILED = 'FAILED', 'Failed / Network Error'

    class Channel(models.TextChoices):
        WHATSAPP = 'WHATSAPP', 'WhatsApp'
        SMS = 'SMS', 'SMS'

    rule = models.ForeignKey(AutomatedNotificationRule, on_delete=models.SET_NULL, null=True, blank=True, related_name='queued_items')
    recipient_name = models.CharField(max_length=150)
    recipient_phone = models.CharField(max_length=30)
    student_ref = models.CharField(max_length=100, blank=True)
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.WHATSAPP)
    message_text = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_log = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    dispatched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification Dispatch Queue Item'
        verbose_name_plural = 'Notification Dispatch Queue'

    def __str__(self):
        return f"[{self.status}] {self.get_channel_display()} to {self.recipient_name} ({self.recipient_phone})"
