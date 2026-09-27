from django.contrib import admin
from .models import SyllabusChapter, SyllabusTopic


class SyllabusTopicInline(admin.TabularInline):
    model = SyllabusTopic
    extra = 2


@admin.register(SyllabusChapter)
class SyllabusChapterAdmin(admin.ModelAdmin):
    list_display = ('class_room', 'subject', 'chapter_number', 'title', 'progress_pct')
    list_filter = ('class_room', 'subject')
    inlines = [SyllabusTopicInline]


@admin.register(SyllabusTopic)
class SyllabusTopicAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'topic_number', 'title', 'status', 'completion_date')
    list_filter = ('status', 'chapter__class_room', 'chapter__subject')
    list_editable = ('status', 'completion_date')
