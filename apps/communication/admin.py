from django.contrib import admin
from .models import Announcement, MessageTemplate, DirectMessageLog


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'audience', 'target_class', 'publish_date', 'is_published', 'author')
    list_filter = ('priority', 'audience', 'is_published', 'publish_date')
    search_fields = ('title', 'content')


@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('title', 'body')


@admin.register(DirectMessageLog)
class DirectMessageLogAdmin(admin.ModelAdmin):
    list_display = ('recipient_name', 'recipient_phone', 'channel', 'recipient_type', 'status', 'sent_by', 'sent_at')
    list_filter = ('channel', 'recipient_type', 'status', 'sent_at')
    search_fields = ('recipient_name', 'recipient_phone', 'message_body')
