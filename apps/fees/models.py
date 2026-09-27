from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.students.models import Student


class FeeCategory(models.Model):
    name = models.CharField(max_length=100, help_text="e.g. Monthly Tuition Fee, Admission Fee, Exam Fee, Transport Fee")
    code = models.CharField(max_length=30, unique=True, help_text="e.g. TUI, ADM, EXM, TRN, LAB, LAT")
    description = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=True, help_text="Is this a recurring monthly fee or a one-off fee?")
    default_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Fee Category'
        verbose_name_plural = 'Fee Categories'

    def __str__(self):
        return f"{self.name} ({self.code})"


class FeeStructure(models.Model):
    class Frequency(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        ANNUAL = 'ANNUAL', 'Annual'
        ONE_TIME = 'ONE_TIME', 'One-Time / Admission'

    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='fee_structures')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='fee_structures')
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='structures')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base standard amount for this class")
    frequency = models.CharField(max_length=20, choices=Frequency.choices, default=Frequency.MONTHLY)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['class_room__numeric_level', 'fee_category__name']
        unique_together = ('academic_year', 'class_room', 'fee_category')
        verbose_name = 'Class Fee Structure'
        verbose_name_plural = 'Class Fee Structures'

    def __str__(self):
        return f"{self.class_room.name} - {self.fee_category.name}: Rs. {self.amount}"


class StudentDiscount(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'Percentage (%)'
        FIXED_AMOUNT = 'FIXED_AMOUNT', 'Fixed Amount (Rs.)'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_discounts')
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, null=True, blank=True, help_text="Apply to specific fee or leave empty for total monthly fee")
    discount_type = models.CharField(max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE)
    value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Percentage (e.g. 50.00 for 50%) or Fixed Rs amount")
    reason = models.CharField(max_length=200, help_text="e.g. Kinship / Sibling Concession, Merit Scholarship, Staff Child, Orphan Aid")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['student', '-created_at']
        verbose_name = 'Student Discount / Concession'
        verbose_name_plural = 'Student Discounts / Concessions'

    def __str__(self):
        val_str = f"{self.value}%" if self.discount_type == self.DiscountType.PERCENTAGE else f"Rs. {self.value}"
        cat_str = f" on {self.fee_category.name}" if self.fee_category else " on Total Monthly Fee"
        return f"{self.student.get_full_name()} - {val_str}{cat_str} ({self.reason})"


class FeeInvoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = 'UNPAID', 'Unpaid'
        PARTIAL = 'PARTIAL', 'Partially Paid'
        PAID = 'PAID', 'Paid'
        OVERDUE = 'OVERDUE', 'Overdue'
        WAIVED = 'WAIVED', 'Waived'

    invoice_number = models.CharField(max_length=50, unique=True, help_text="e.g. INV-2026-0001")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='fee_invoices')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name='fee_invoices')
    class_room = models.ForeignKey(ClassRoom, on_delete=models.PROTECT, related_name='class_invoices')
    section = models.ForeignKey(Section, on_delete=models.PROTECT, null=True, blank=True, related_name='section_invoices')
    
    fee_month = models.CharField(max_length=30, help_text="e.g. January 2026, Admission Fee, Annual Charges")
    fee_year = models.PositiveIntegerField(default=2026)
    issue_date = models.DateField()
    due_date = models.DateField()

    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Sum of all fee heads before concession")
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Total concessions/scholarship applied")
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Late payment fine/surcharge")
    payable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Net amount to be paid")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Total amount collected")
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Remaining unpaid balance")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-due_date', '-created_at']
        verbose_name = 'Fee Invoice / Challan'
        verbose_name_plural = 'Fee Invoices / Challans'

    def __str__(self):
        return f"{self.invoice_number} - {self.student.get_full_name()} ({self.fee_month}) - Rs. {self.payable_amount}"

    def recalculate_totals(self):
        """Helper to recalculate total payable, balance and update payment status"""
        items_total = sum(item.amount for item in self.items.all())
        self.subtotal_amount = items_total
        net = (self.subtotal_amount - self.discount_amount) + self.fine_amount
        self.payable_amount = max(Decimal('0.00'), net)
        
        # Calculate total payments made
        total_paid = sum(p.amount for p in self.payments.all())
        self.paid_amount = total_paid
        self.balance_amount = max(Decimal('0.00'), self.payable_amount - self.paid_amount)
        
        if self.balance_amount == Decimal('0.00') and self.payable_amount > Decimal('0.00'):
            self.status = self.Status.PAID
        elif self.paid_amount > Decimal('0.00') and self.balance_amount > Decimal('0.00'):
            self.status = self.Status.PARTIAL
        elif self.status != self.Status.WAIVED:
            from datetime import date
            if self.due_date < date.today() and self.paid_amount == Decimal('0.00'):
                self.status = self.Status.OVERDUE
            else:
                self.status = self.Status.UNPAID
        self.save()


class FeeInvoiceItem(models.Model):
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='items')
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name='invoice_items')
    description = models.CharField(max_length=150, help_text="e.g. Monthly Tuition, Lab Maintenance, Exam Paper Fund")
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.description}: Rs. {self.amount}"


class FeePayment(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer / Online Deposit'
        CHEQUE = 'CHEQUE', 'Cheque / Pay Order'
        EASYPAISA_JAZZCASH = 'EASYPAISA_JAZZCASH', 'Easypaisa / JazzCash'
        OTHER = 'OTHER', 'Other'

    receipt_number = models.CharField(max_length=50, unique=True, help_text="e.g. REC-2026-0001")
    invoice = models.ForeignKey(FeeInvoice, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name='fee_payments')
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    transaction_reference = models.CharField(max_length=100, blank=True, null=True, help_text="Bank Slip No, Cheque No, or Mobile Wallet TxID")
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_payments')
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'Fee Payment / Receipt'
        verbose_name_plural = 'Fee Payments / Receipts'

    def __str__(self):
        return f"{self.receipt_number} - {self.student.get_full_name()} (Rs. {self.amount} via {self.get_payment_method_display()})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Automatically update the associated invoice balance and status
        self.invoice.recalculate_totals()
