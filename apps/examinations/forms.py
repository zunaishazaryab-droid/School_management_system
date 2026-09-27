from django import forms
from .models import Exam, ExamSchedule, ExamMarks, GradeScale
from apps.academics.models import AcademicYear, ClassRoom, Subject


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['title', 'exam_type', 'academic_year', 'start_date', 'end_date', 'is_published', 'is_active', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mid-Term Examination 2026'}),
            'exam_type': forms.Select(attrs={'class': 'form-control'}),
            'academic_year': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional exam notes / instructions...'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class ExamScheduleForm(forms.ModelForm):
    class Meta:
        model = ExamSchedule
        fields = ['exam', 'class_room', 'subject', 'exam_date', 'start_time', 'end_time', 'total_marks', 'passing_marks', 'room_number']
        widgets = {
            'exam': forms.Select(attrs={'class': 'form-control'}),
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'exam_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'passing_marks': forms.NumberInput(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hall A, Room 102'}),
        }


class GradeScaleForm(forms.ModelForm):
    class Meta:
        model = GradeScale
        fields = ['name', 'min_percentage', 'max_percentage', 'grade_point', 'remarks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A+'}),
            'min_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'max_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'grade_point': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Outstanding / Distinction'}),
        }
