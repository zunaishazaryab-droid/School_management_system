from django.contrib import admin
from .models import FeeCategory, FeeStructure, StudentDiscount, FeeInvoice, FeeInvoiceItem, FeePayment


class FeeInvoiceItemInline(admin.TabularInline):
    model = FeeInvoiceItem
    extra = 1


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ('receipt_number', 'payment_date', 'amount', 'payment_method', 'received_by')


@admin.register(FeeCategory)
class FeeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'default_amount', 'is_recurring', 'is_active')
    search_fields = ('name', 'code')


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('class_room', 'fee_category', 'amount', 'frequency', 'academic_year')
    list_filter = ('class_room', 'academic_year', 'frequency')


@admin.register(StudentDiscount)
class StudentDiscountAdmin(admin.ModelAdmin):
    list_display = ('student', 'discount_type', 'value', 'fee_category', 'reason', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('student__first_name', 'student__last_name', 'student__admission_number', 'reason')


@admin.register(FeeInvoice)
class FeeInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'student', 'class_room', 'fee_month', 'payable_amount', 'paid_amount', 'balance_amount', 'status', 'due_date')
    list_filter = ('status', 'class_room', 'fee_year', 'academic_year')
    search_fields = ('invoice_number', 'student__first_name', 'student__last_name', 'student__admission_number')
    inlines = [FeeInvoiceItemInline, FeePaymentInline]


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'student', 'invoice', 'amount', 'payment_method', 'payment_date', 'received_by')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('receipt_number', 'student__first_name', 'student__last_name', 'student__admission_number', 'transaction_reference')
