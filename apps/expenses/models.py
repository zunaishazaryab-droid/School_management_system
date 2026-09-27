from django.db import models
from django.conf import settings
from decimal import Decimal


class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Staff Salaries, Electricity, Rent, Stationery, Maintenance, Events")
    code = models.CharField(max_length=30, unique=True, help_text="e.g. SAL, ELE, RNT, STN, MNT, EVT, MISC")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer / Cheque'
        ONLINE = 'ONLINE', 'Online / Mobile Banking'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        PAID = 'PAID', 'Paid / Cleared'
        PENDING = 'PENDING', 'Pending Approval'
        CANCELLED = 'CANCELLED', 'Cancelled / Void'

    expense_number = models.CharField(max_length=50, unique=True, help_text="e.g. EXP-2026-0001")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses')
    title = models.CharField(max_length=200, help_text="Brief description e.g. Monthly Electricity Bill for Campus 1")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Amount in Rs.")
    expense_date = models.DateField(help_text="Date expense occurred")
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    payee_name = models.CharField(max_length=150, help_text="Vendor, Service Provider, or Staff Name")
    receipt_document = models.FileField(upload_to='expense_receipts/', blank=True, null=True, help_text="Upload scanned bill or receipt")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_expenses')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PAID)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = 'Expense'
        verbose_name_plural = 'Expenses'

    def __str__(self):
        return f"{self.expense_number} - {self.title} (Rs. {self.amount})"
