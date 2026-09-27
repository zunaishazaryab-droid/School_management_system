from django import forms
from .models import AcademicYear, ClassRoom, Section, Subject, ClassSubject


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model = AcademicYear
        fields = ['name', 'start_date', 'end_date', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2026-2027'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ['name', 'code', 'numeric_level', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Class 1'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. C1'}),
            'numeric_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['class_room', 'name', 'capacity', 'class_teacher']
        widgets = {
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A or Rose'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '40'}),
            'class_teacher': forms.Select(attrs={'class': 'form-control'}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'total_marks', 'passing_marks', 'is_elective', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mathematics'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. MATH-01'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_elective': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ['class_room', 'section', 'subject', 'teacher']
        widgets = {
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
        }
