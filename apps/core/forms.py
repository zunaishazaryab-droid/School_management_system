from django import forms
from .models import SchoolSetting
from apps.accounts.models import User


class SchoolSettingForm(forms.ModelForm):
    class Meta:
        model = SchoolSetting
        fields = [
            'school_name', 'tagline', 'logo', 'phone', 
            'email', 'address', 'current_academic_session', 'currency_symbol'
        ]
        widgets = {
            'school_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Elite Model High School'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Knowledge, Excellence & Integrity'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 300 1234567'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'info@eliteschool.edu.pk'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Campus location, city...'}),
            'current_academic_session': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '2026-2027'}),
            'currency_symbol': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Rs.'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class SystemUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter strong password'}),
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone_number', 'password', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username (e.g. admin_tariq)'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@eliteschool.edu.pk'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+92 300 1234567'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
