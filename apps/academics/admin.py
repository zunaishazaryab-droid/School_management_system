from django.contrib import admin
from .models import AcademicYear, ClassRoom, Section, Subject, ClassSubject


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_editable = ('is_current',)


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'numeric_level')
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('class_room', 'name', 'capacity', 'class_teacher')
    list_filter = ('class_room',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'total_marks', 'passing_marks', 'is_elective')
    search_fields = ('name', 'code')


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ('class_room', 'section', 'subject', 'teacher')
    list_filter = ('class_room', 'subject')
