from django import forms
from .models import Book, BookCategory, BookIssue


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'isbn', 'publisher', 'edition', 'category', 'rack_location', 'total_copies', 'available_copies', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Book Title'}),
            'author': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author Name'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '978-3-16-148410-0'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Publisher Name'}),
            'edition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2nd Revised Edition'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'rack_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Shelf A-3, Rack 12'}),
            'total_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'available_copies': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class BookIssueForm(forms.ModelForm):
    class Meta:
        model = BookIssue
        fields = ['book', 'student', 'issue_date', 'due_date', 'remarks']
        widgets = {
            'book': forms.Select(attrs={'class': 'form-control'}),
            'student': forms.Select(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional condition notes'}),
        }
