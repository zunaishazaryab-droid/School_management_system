from django.contrib import admin
from .models import GradeScale, Exam, ExamSchedule, ExamMarks, ExamStudentResult


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_percentage', 'max_percentage', 'grade_point', 'remarks')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam_type', 'academic_year', 'start_date', 'end_date', 'is_published', 'is_active')
    list_filter = ('exam_type', 'academic_year', 'is_published', 'is_active')


@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('exam', 'class_room', 'subject', 'exam_date', 'total_marks', 'passing_marks')
    list_filter = ('exam', 'class_room')


@admin.register(ExamMarks)
class ExamMarksAdmin(admin.ModelAdmin):
    list_display = ('exam_schedule', 'student', 'marks_obtained', 'is_absent', 'recorded_by')
    list_filter = ('exam_schedule__exam', 'exam_schedule__class_room', 'is_absent')


@admin.register(ExamStudentResult)
class ExamStudentResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'class_room', 'section', 'percentage', 'grade', 'position_in_section', 'is_passed')
    list_filter = ('exam', 'class_room', 'grade', 'is_passed')
