from django import forms
from .models import Student, StudentDocument, StudentPromotionHistory
from apps.academics.models import ClassRoom, Section, AcademicYear


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'admission_number', 'roll_number', 'current_class', 'current_section', 'academic_year',
            'admission_date', 'status',
            'first_name', 'last_name', 'gender', 'date_of_birth', 'blood_group', 'religion', 'nationality',
            'guardian_name', 'guardian_relationship', 'guardian_cnic', 'guardian_phone', 'emergency_contact',
            'guardian_email', 'guardian_occupation', 'residential_address', 'city',
            'previous_school', 'medical_notes', 'photo', 'biometric_id'
        ]
        widgets = {
            'admission_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. STU-2026-001'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 101'}),
            'current_class': forms.Select(attrs={'class': 'form-control', 'id': 'id_current_class'}),
            'current_section': forms.Select(attrs={'class': 'form-control', 'id': 'id_current_section'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'admission_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B+'}),
            'religion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Islam'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pakistani'}),

            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father or Guardian Full Name'}),
            'guardian_relationship': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Father'}),
            'guardian_cnic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 61101-1234567-1'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 300 1234567'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 312 9876543'}),
            'guardian_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'parent@example.com'}),
            'guardian_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Business, Engineer'}),
            'residential_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Complete home address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),

            'previous_school': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Previous school attended (if any)'}),
            'medical_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Allergies, chronic conditions, emergency medical instructions'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'biometric_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional hardware ID (Reserved for future)'}),
        }


class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ['title', 'document_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. B-Form Copy, Previous Leaving Certificate'}),
            'document_file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudentPromotionForm(forms.Form):
    ACTION_CHOICES = [
        ('PROMOTE', '⬆️ Promote to Higher Class'),
        ('DEMOTE', '⬇️ Demote to Lower / Previous Class'),
    ]
    action_type = forms.ChoiceField(
        choices=ACTION_CHOICES,
        initial='PROMOTE',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Action Type"
    )
    from_class = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'promo_from_class'}),
        label="Source Class"
    )
    from_section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="From Section (Optional)"
    )
    to_class = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Destination Target Class"
    )
    to_section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Target Section"
    )
    target_academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Target Academic Session"
    )
    remarks = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Annual Promotion Session 2026-2027 / Academic Review'}),
        required=False
    )


class SingleStudentPromoteDemoteForm(forms.Form):
    ACTION_CHOICES = [
        ('PROMOTE', '⬆️ Promote Student (Higher Class)'),
        ('DEMOTE', '⬇️ Demote Student (Lower / Previous Class)'),
    ]
    action_type = forms.ChoiceField(
        choices=ACTION_CHOICES,
        initial='PROMOTE',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'single_action_type'}),
        label="Action"
    )
    to_class = forms.ModelChoiceField(
        queryset=ClassRoom.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Target Class"
    )
    to_section = forms.ModelChoiceField(
        queryset=Section.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Target Section"
    )
    target_academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Academic Session"
    )
    roll_number = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'New Roll Number (optional)'}),
        label="Roll Number"
    )
    remarks = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Promoted after passing Annual Exams / Demoted for foundational support'}),
        required=False
    )

