from django import forms
from .models import SyllabusChapter, SyllabusTopic


class SyllabusChapterForm(forms.ModelForm):
    class Meta:
        model = SyllabusChapter
        fields = ['class_room', 'subject', 'chapter_number', 'title', 'description']
        widgets = {
            'class_room': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.Select(attrs={'class': 'form-control'}),
            'chapter_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Chapter 4: Photosynthesis'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class SyllabusTopicForm(forms.ModelForm):
    class Meta:
        model = SyllabusTopic
        fields = ['chapter', 'topic_number', 'title', 'estimated_periods', 'status', 'completion_date', 'teacher_notes']
        widgets = {
            'chapter': forms.Select(attrs={'class': 'form-control'}),
            'topic_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 4.1'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Light and Dark reactions'}),
            'estimated_periods': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'completion_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'teacher_notes': forms.TextInput(attrs={'class': 'form-control'}),
        }
