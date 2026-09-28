from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.students.models import Student


class BookCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Science, Mathematics, English Literature, Islamic Studies, History")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. SCI, MAT, ENG, ISL")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Book Category'
        verbose_name_plural = 'Book Categories'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Book(models.Model):
    title = models.CharField(max_length=200, help_text="Book Title")
    author = models.CharField(max_length=150, help_text="Author(s)")
    isbn = models.CharField(max_length=50, blank=True, null=True, help_text="ISBN / Barcode number")
    publisher = models.CharField(max_length=150, blank=True)
    edition = models.CharField(max_length=50, default='1st Edition', blank=True)
    category = models.ForeignKey(BookCategory, on_delete=models.CASCADE, related_name='books')
    rack_location = models.CharField(max_length=50, help_text="e.g. Shelf A-3, Rack 12")
    total_copies = models.PositiveIntegerField(default=5)
    available_copies = models.PositiveIntegerField(default=5)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('500.00'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Library Book'
        verbose_name_plural = 'Library Books'

    def __str__(self):
        return f"{self.title} by {self.author} (Shelf: {self.rack_location})"


class BookIssue(models.Model):
    class Status(models.TextChoices):
        ISSUED = 'ISSUED', 'Issued / Borrowed'
        RETURNED = 'RETURNED', 'Returned'
        OVERDUE = 'OVERDUE', 'Overdue'
        LOST = 'LOST', 'Lost / Damaged'

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issued_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True, related_name='borrowed_books')
    issue_date = models.DateField()
    due_date = models.DateField()
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ISSUED)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-issue_date']
        verbose_name = 'Book Issuance'
        verbose_name_plural = 'Book Issuance Records'

    def __str__(self):
        return f"'{self.book.title}' issued to {self.student.get_full_name() if self.student else 'Staff'}"
