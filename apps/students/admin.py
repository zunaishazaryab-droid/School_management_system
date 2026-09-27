from django.contrib import admin
from .models import Student, StudentDocument, StudentPromotionHistory


class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'first_name', 'last_name', 'current_class', 'current_section', 'guardian_phone', 'status')
    list_filter = ('current_class', 'current_section', 'status', 'gender')
    search_fields = ('admission_number', 'first_name', 'last_name', 'guardian_name', 'guardian_phone')
    inlines = [StudentDocumentInline]


@admin.register(StudentPromotionHistory)
class StudentPromotionHistoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_class', 'to_class', 'promotion_date', 'promoted_by')
    list_filter = ('from_class', 'to_class', 'promotion_date')
