from django import forms
from .models import Vehicle, Route, RouteStop, StudentTransportAllocation


class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['vehicle_number', 'model_name', 'seating_capacity', 'driver_name', 'driver_phone', 'driver_license_number', 'status', 'notes']
        widgets = {
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ICT-LEA-1234'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Toyota HiAce 2024'}),
            'seating_capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'driver_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Driver Full Name'}),
            'driver_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '03001234567'}),
            'driver_license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'License No.'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['title', 'start_point', 'end_point', 'monthly_fare', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Route A: G-10 to Campus via F-10'}),
            'start_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sector G-10'}),
            'end_point': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Main Campus'}),
            'monthly_fare': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AllocationForm(forms.ModelForm):
    class Meta:
        model = StudentTransportAllocation
        fields = ['student', 'vehicle', 'route', 'stop', 'start_date', 'monthly_fee', 'status', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'route': forms.Select(attrs={'class': 'form-control'}),
            'stop': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
        }
