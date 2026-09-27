from django import forms
from decimal import Decimal
from .models import FeeCategory, FeeStructure, StudentDiscount, FeeInvoice, FeeInvoiceItem, FeePayment
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.students.models import Student


class FeeCategoryForm(forms.ModelForm):
    class Meta:
        model = FeeCategory
        fields = ['name', 'code', 'default_amount', 'is_recurring', 'is_active', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monthly Tuition Fee'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. TUI'}),
            'default_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description and guidelines...'}),
            'is_recurring': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['academic_year', 'class_room', 'fee_category', 'amount', 'frequency']
        widgets = {
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'fee_category': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount in Rs.'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
        }


class StudentDiscountForm(forms.ModelForm):
    class Meta:
        model = StudentDiscount
        fields = ['student', 'fee_category', 'discount_type', 'value', 'reason', 'is_active']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'fee_category': forms.Select(attrs={'class': 'form-control'}),
            'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Percentage (e.g. 25) or Rs.'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Sibling Kinship Concession (25%)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class GenerateBulkInvoicesForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Select target session"
    )
    class_room = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Leave blank to generate for ALL active classes"
    )
    fee_month = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. October 2026'}),
        help_text="Month or billing title"
    )
    fee_year = forms.IntegerField(
        initial=2026,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    issue_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    apply_discounts = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        help_text="Automatically calculate and deduct active student concessions/scholarships"
    )


class SingleInvoiceForm(forms.ModelForm):
    class Meta:
        model = FeeInvoice
        fields = ['student', 'academic_year', 'class_room', 'section', 'fee_month', 'fee_year', 'issue_date', 'due_date', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control', 'id': 'studentSelect'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'fee_month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. November 2026'}),
            'fee_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional invoice remarks...'}),
        }


class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ['amount', 'payment_date', 'payment_method', 'transaction_reference', 'remarks']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Amount in Rs.'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'transaction_reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional Bank Slip / TxID / Cheque #'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional payment note'}),
        }
