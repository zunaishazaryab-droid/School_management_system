from django import forms
from .models import InventoryItem, StockTransaction, Supplier, ItemCategory


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'item_code', 'category', 'quantity_in_stock', 'min_reorder_level', 'unit', 'unit_price', 'location', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. A4 Printing Paper Reams'}),
            'item_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. STAT-001'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'min_reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Main Store Room - Cupboard B'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Item specifications or brand details'}),
        }


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['item', 'transaction_type', 'quantity', 'unit_price', 'supplier', 'issued_to', 'reference_number', 'transaction_date', 'notes']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'issued_to': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Science Lab / Sir Ahmad'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. PO-8492 or REC-102'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional transaction remarks'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Supplier Company / Business Name'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Representative Name'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone / Mobile Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'supplier@example.com'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Business location address'}),
        }


class ItemCategoryForm(forms.ModelForm):
    class Meta:
        model = ItemCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Stationery, Uniform, Lab Equipment'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Category description...'}),
        }

