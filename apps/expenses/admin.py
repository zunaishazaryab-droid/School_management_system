from django.contrib import admin
from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('expense_number', 'title', 'category', 'amount', 'expense_date', 'payment_method', 'payee_name', 'status')
    list_filter = ('category', 'status', 'payment_method', 'expense_date')
    search_fields = ('expense_number', 'title', 'payee_name')
