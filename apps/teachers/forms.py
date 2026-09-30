from django import forms
from .models import Teacher, SalaryPayment, StaffLeave, TeacherPerformance
from apps.accounts.models import User


class TeacherForm(forms.ModelForm):
    # Embedded user account fields
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'teacher@beaconheights.edu.pk'}))
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))

    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'staff_type', 'designation', 'department', 'qualification', 'experience_years',
            'joining_date', 'basic_salary', 'cnic', 'phone_number', 'emergency_contact',
            'residential_address', 'status', 'photo'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EMP-2026-001'}),
            'staff_type': forms.Select(attrs={'class': 'form-control'}),
            'designation': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Science / Mathematics'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. M.Sc Mathematics, B.Ed'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '45000'}),
            'cnic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 61101-1234567-3'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 300 1234567'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 312 9876543'}),
            'residential_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['teacher', 'salary_month', 'basic_salary', 'allowances', 'deductions', 'payment_date', 'payment_method', 'status', 'remarks']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'salary_month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. April 2026'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'allowances': forms.NumberInput(attrs={'class': 'form-control'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
        }


class StaffLeaveForm(forms.ModelForm):
    class Meta:
        model = StaffLeave
        fields = ['teacher', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'leave_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'State reason for leave...'}),
        }


class TeacherPerformanceForm(forms.ModelForm):
    class Meta:
        model = TeacherPerformance
        fields = [
            'teacher', 'evaluation_month', 'punctuality_rating', 
            'syllabus_coverage_pct', 'homework_regularity_pct', 
            'copies_checked_pct', 'overall_score', 'coordinator_remarks'
        ]
        widgets = {
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'evaluation_month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. September 2026'}),
            'punctuality_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'e.g. 95'}),
            'syllabus_coverage_pct': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'e.g. 88'}),
            'homework_regularity_pct': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'e.g. 90'}),
            'copies_checked_pct': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'placeholder': 'e.g. 92'}),
            'overall_score': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': 0, 'max': 10, 'placeholder': 'e.g. 9.1'}),
            'coordinator_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Evaluator qualitative assessment, observations, strengths and improvement areas...'}),
        }

