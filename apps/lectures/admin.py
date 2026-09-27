from django.contrib import admin
from .models import DailyLecture, Homework


@admin.register(DailyLecture)
class DailyLectureAdmin(admin.ModelAdmin):
    list_display = ('date', 'class_room', 'section', 'subject', 'teacher', 'topic', 'copies_checked_count')
    list_filter = ('date', 'class_room', 'subject', 'teacher')
    search_fields = ('topic', 'chapter_name', 'classwork_description')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_room', 'section', 'subject', 'assigned_date', 'due_date', 'status')
    list_filter = ('class_room', 'subject', 'status', 'assigned_date')
