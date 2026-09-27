from django import forms
from .models import DailyLecture, Homework


class DailyLectureForm(forms.ModelForm):
    class Meta:
        model = DailyLecture
        fields = [
            'date', 'class_room', 'section', 'subject', 'chapter_name', 'topic',
            'learning_objectives', 'classwork_description', 'homework_assigned',
            'present_students_count', 'absent_students_count', 'copies_checked_count', 'remarks'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'class_room': forms.Select(attrs={'class': 'form-control', 'id': 'id_lecture_class'}),
            'section': forms.Select(attrs={'class': 'form-control', 'id': 'id_lecture_section'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'chapter_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Chapter 3: Linear Equations'}),
            'topic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Graphical solution of simultaneous equations'}),
            'learning_objectives': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Key concepts taught...'}),
            'classwork_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Problems solved on whiteboard...'}),
            'homework_assigned': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Assigned textbook exercises...'}),
            'present_students_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'absent_students_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'copies_checked_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Class discipline, pace remarks...'}),
        }


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['class_room', 'section', 'subject', 'title', 'description', 'assigned_date', 'due_date', 'status', 'attachment']
        widgets = {
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Science Chapter 2 Review Questions'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Complete questions 1 to 8 on homework copy...'}),
            'assigned_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }
