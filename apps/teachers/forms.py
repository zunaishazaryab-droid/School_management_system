from django import forms
from decimal import Decimal
from .models import Teacher, SalaryPayment, StaffLeave, TeacherPerformance
from apps.accounts.models import User


class TeacherForm(forms.ModelForm):
    # Embedded user account fields
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_first_name', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_last_name', 'placeholder': 'Last Name'}))
    email = forms.CharField(max_length=254, required=False, widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'id_email', 'placeholder': 'staff@genxvision.edu.pk'}))
    username = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_username', 'placeholder': 'Auto-generated username'}))

    class Meta:
        model = Teacher
        fields = [
            'employee_id', 'staff_type', 'designation', 'department', 'qualification', 'experience_years',
            'joining_date', 'basic_salary', 'cnic', 'phone_number', 'emergency_contact',
            'residential_address', 'status', 'photo'
        ]
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_employee_id', 'placeholder': 'e.g. EMP-2026-001'}),
            'staff_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_staff_type', 'onchange': 'onStaffTypeChange()'}),
            'designation': forms.Select(attrs={'class': 'form-control', 'id': 'id_designation'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_department', 'placeholder': 'e.g. Science / Mathematics'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_qualification', 'placeholder': 'e.g. M.Sc Mathematics, B.Ed'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_experience_years', 'min': '0'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'id': 'id_joining_date', 'type': 'date'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_basic_salary', 'placeholder': '45000'}),
            'cnic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 61101-1234567-3'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_phone_number', 'placeholder': '+92 300 1234567'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 312 9876543'}),
            'residential_address': forms.Textarea(attrs={'class': 'form-control', 'id': 'id_residential_address', 'rows': 2, 'placeholder': 'Residential address / city'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['employee_id'].required = False
        self.fields['department'].required = False
        self.fields['qualification'].required = False
        self.fields['experience_years'].required = False
        self.fields['joining_date'].required = False
        self.fields['basic_salary'].required = False
        self.fields['phone_number'].required = False
        self.fields['residential_address'].required = False
        self.fields['status'].required = False
        self.fields['status'].initial = Teacher.Status.ACTIVE

        if self.instance and self.instance.pk and hasattr(self.instance, 'user'):
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['username'].initial = self.instance.user.username

    def clean_employee_id(self):
        emp_id = self.cleaned_data.get('employee_id', '').strip()
        if not emp_id:
            return ''
        qs = Teacher.objects.filter(employee_id__iexact=emp_id)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            # Silently auto-resolve collision with a clean suffix so user never encounters an error
            base_id = emp_id
            counter = 2
            while Teacher.objects.filter(employee_id__iexact=f"{base_id}-{counter}").exists():
                counter += 1
            emp_id = f"{base_id}-{counter}"
        return emp_id

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if username:
            import re
            # Replace spaces and special characters with underscore
            username = re.sub(r'[^a-zA-Z0-9_]', '_', username.replace(' ', '_')).lower()
            username = re.sub(r'_+', '_', username).strip('_')
        return username

    def clean_email(self):
        raw_email = self.cleaned_data.get('email', '').strip()
        if not raw_email:
            return ''
        import re
        if '@' in raw_email:
            parts = raw_email.split('@', 1)
            clean_local = re.sub(r'[^a-zA-Z0-9._-]', '_', parts[0].replace(' ', '_')).strip('_')
            clean_local = re.sub(r'_+', '_', clean_local)
            clean_domain = re.sub(r'[^a-zA-Z0-9.-]', '', parts[1].replace(' ', ''))
            return f"{clean_local}@{clean_domain}"
        else:
            clean_local = re.sub(r'[^a-zA-Z0-9._-]', '_', raw_email.replace(' ', '_')).strip('_')
            clean_local = re.sub(r'_+', '_', clean_local)
            return f"{clean_local}@genxvision.edu.pk"

    def clean(self):
        cleaned_data = super().clean()
        from django.utils import timezone
        import random
        import re

        first_name = cleaned_data.get('first_name', '').strip()
        if not first_name:
            first_name = 'Staff'
            cleaned_data['first_name'] = first_name

        employee_id = cleaned_data.get('employee_id', '').strip()
        if not employee_id:
            year = timezone.now().year
            # Find a unique employee ID that doesn't exist yet
            while True:
                rand_suffix = random.randint(1000, 9999)
                candidate_id = f"EMP-{year}-{rand_suffix}"
                if not Teacher.objects.filter(employee_id=candidate_id).exists():
                    employee_id = candidate_id
                    break
            cleaned_data['employee_id'] = employee_id

        staff_type = cleaned_data.get('staff_type', Teacher.StaffType.TEACHING)
        
        # Clean and auto-generate username if blank
        username = cleaned_data.get('username', '').strip()
        if not username:
            clean_name = re.sub(r'[^a-zA-Z0-9]', '', first_name.lower()) or 'staff'
            clean_emp = re.sub(r'[^a-zA-Z0-9]', '', employee_id.lower()) or str(random.randint(1000, 9999))
            username = f"{clean_name}_{clean_emp}"
            cleaned_data['username'] = username

        # Clean and auto-generate email if blank
        email = cleaned_data.get('email', '').strip()
        if not email:
            cleaned_data['email'] = f"{username}@genxvision.edu.pk"

        # Defaults for other fields
        if not cleaned_data.get('status'):
            cleaned_data['status'] = Teacher.Status.ACTIVE

        if not cleaned_data.get('qualification'):
            cleaned_data['qualification'] = 'N/A' if staff_type == Teacher.StaffType.NON_TEACHING else 'B.Ed / Graduation'

        if not cleaned_data.get('department') or (staff_type == Teacher.StaffType.NON_TEACHING and cleaned_data.get('department') == 'Academics'):
            designation = cleaned_data.get('designation')
            if staff_type == Teacher.StaffType.NON_TEACHING:
                dept_map = {
                    'ACCOUNTANT': 'Finance & Accounts',
                    'ADMIN_OFFICER': 'Administration & Records',
                    'LIBRARIAN': 'Library & Learning Resource',
                    'IT_SUPPORT': 'IT & Computer Lab Support',
                    'RECEPTIONIST': 'Front Desk & Reception',
                    'SECURITY_GUARD': 'Security & Campus Safety',
                    'DRIVER': 'Transport & Fleet',
                    'SUPPORT_STAFF': 'General Support & Caretaking',
                    'MAINTENANCE': 'Campus Maintenance & Electrical',
                }
                cleaned_data['department'] = dept_map.get(designation, 'Administration & Support')
            else:
                cleaned_data['department'] = 'Academics'

        if cleaned_data.get('experience_years') is None:
            cleaned_data['experience_years'] = 1 if staff_type == Teacher.StaffType.NON_TEACHING else 2

        if not cleaned_data.get('joining_date'):
            cleaned_data['joining_date'] = timezone.now().date()

        if not cleaned_data.get('basic_salary'):
            cleaned_data['basic_salary'] = Decimal('25000.00') if staff_type == Teacher.StaffType.NON_TEACHING else Decimal('45000.00')

        if not cleaned_data.get('phone_number'):
            cleaned_data['phone_number'] = '+92 300 0000000'

        if not cleaned_data.get('residential_address'):
            cleaned_data['residential_address'] = 'Local Campus'

        return cleaned_data


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

