from django.contrib import admin
from .models import StudentAttendance, TeacherAttendance


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'class_room', 'section', 'status', 'recorded_by')
    list_filter = ('date', 'class_room', 'section', 'status')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number')


@admin.register(TeacherAttendance)
class TeacherAttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'teacher', 'status', 'check_in_time', 'check_out_time', 'recorded_by')
    list_filter = ('date', 'status')
