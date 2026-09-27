from django.contrib import admin
from .models import Teacher, SalaryPayment, StaffLeave, TeacherPerformance


class SalaryPaymentInline(admin.TabularInline):
    model = SalaryPayment
    extra = 0


class StaffLeaveInline(admin.TabularInline):
    model = StaffLeave
    extra = 0


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_name', 'designation', 'department', 'phone_number', 'basic_salary', 'status')
    list_filter = ('designation', 'department', 'status')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__username', 'phone_number')
    inlines = [SalaryPaymentInline, StaffLeaveInline]

    def get_name(self, obj):
        return obj.get_full_name()
    get_name.short_description = 'Faculty Name'


@admin.register(SalaryPayment)
class SalaryPaymentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'salary_month', 'basic_salary', 'allowances', 'deductions', 'net_salary', 'status', 'payment_date')
    list_filter = ('salary_month', 'status', 'payment_method')


@admin.register(StaffLeave)
class StaffLeaveAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'leave_type', 'start_date', 'end_date', 'status', 'approved_by')
    list_filter = ('leave_type', 'status')


@admin.register(TeacherPerformance)
class TeacherPerformanceAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'evaluation_month', 'punctuality_rating', 'syllabus_coverage_pct', 'overall_score')
    list_filter = ('evaluation_month',)
