from django import forms
from .models import Announcement, MessageTemplate, DirectMessageLog
from apps.academics.models import ClassRoom, Section


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = [
            'title', 'content', 'priority', 'audience', 
            'target_class', 'target_section', 'attachment', 
            'publish_date', 'expiry_date', 'is_published'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Annual Sports Gala Notice'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Write circular details, timings, dress code, instructions...'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'audience': forms.Select(attrs={'class': 'form-control'}),
            'target_class': forms.Select(attrs={'class': 'form-control'}),
            'target_section': forms.Select(attrs={'class': 'form-control'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'publish_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MessageTemplateForm(forms.ModelForm):
    class Meta:
        model = MessageTemplate
        fields = ['title', 'category', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Monthly Fee Recovery SMS'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5, 
                'placeholder': 'Dear {guardian_name}, this is a gentle reminder regarding {student_name} (Class {class_name}). Pending fee for {fee_month} is Rs. {due_amount}. Please pay by {date}.'
            }),
        }


class DirectMessageSendForm(forms.ModelForm):
    class Meta:
        model = DirectMessageLog
        fields = ['recipient_type', 'recipient_name', 'recipient_phone', 'channel', 'template', 'message_body']
        widgets = {
            'recipient_type': forms.Select(attrs={'class': 'form-control'}),
            'recipient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Recipient Full Name'}),
            'recipient_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '03001234567 or 923001234567'}),
            'channel': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'message_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter personalized message...'}),
        }
