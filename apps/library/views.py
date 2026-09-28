from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q

from apps.accounts.decorators import teacher_required, coordinator_required
from apps.core.models import ActivityLog
from .models import Book, BookCategory, BookIssue
from .forms import BookForm, BookIssueForm


@login_required
def library_dashboard_view(request):
    """Library & Book Management Overview"""
    books = Book.objects.select_related('category').all()
    categories = BookCategory.objects.all()
    issues = BookIssue.objects.select_related('book', 'student').all()

    total_titles = books.count()
    total_copies = books.aggregate(total=Sum('total_copies'))['total'] or 0
    available_copies = books.aggregate(total=Sum('available_copies'))['total'] or 0
    active_loans = issues.filter(status=BookIssue.Status.ISSUED).count()
    overdue_loans = issues.filter(status=BookIssue.Status.ISSUED, due_date__lt=timezone.now().date()).count()

    return render(request, 'library/library_dashboard.html', {
        'books': books[:8],
        'categories': categories,
        'recent_issues': issues[:6],
        'total_titles': total_titles,
        'total_copies': total_copies,
        'available_copies': available_copies,
        'active_loans': active_loans,
        'overdue_loans': overdue_loans,
        'page_title': 'Library Management & Book Catalog'
    })


@login_required
@teacher_required
def book_list_view(request):
    books = Book.objects.select_related('category').all()
    query = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category')

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(isbn__icontains=query))
    if cat_id:
        books = books.filter(category_id=cat_id)

    categories = BookCategory.objects.all()
    return render(request, 'library/book_list.html', {
        'books': books,
        'categories': categories,
        'search_query': query,
        'selected_category': cat_id,
        'page_title': 'Library Book Catalog'
    })


@login_required
@coordinator_required
def book_create_view(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            b = form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Library', f"Added book '{b.title}' by {b.author} ({b.total_copies} copies)", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Book '{b.title}' added to library catalog!")
            return redirect('library:book_list')
    else:
        form = BookForm()
    return render(request, 'library/book_form.html', {'form': form, 'page_title': 'Add Book to Catalog'})


@login_required
@teacher_required
def book_issue_list_view(request):
    issues = BookIssue.objects.select_related('book', 'student').all()
    status_filter = request.GET.get('status')
    if status_filter:
        issues = issues.filter(status=status_filter)

    return render(request, 'library/issue_list.html', {
        'issues': issues,
        'status_filter': status_filter,
        'page_title': 'Book Issuance & Return Register'
    })


@login_required
@teacher_required
def book_issue_create_view(request):
    if request.method == 'POST':
        form = BookIssueForm(request.POST)
        if form.is_valid():
            iss = form.save(commit=False)
            iss.issued_by = request.user
            if iss.book.available_copies > 0:
                iss.book.available_copies -= 1
                iss.book.save()
                iss.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Library', f"Issued book '{iss.book.title}' to {iss.student.get_full_name()}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Book '{iss.book.title}' issued successfully!")
                return redirect('library:issue_list')
            else:
                messages.error(request, "No available copies of this book currently in library.")
    else:
        form = BookIssueForm(initial={'issue_date': timezone.now().date(), 'due_date': timezone.now().date() + timezone.timedelta(days=14)})
    return render(request, 'library/issue_form.html', {'form': form, 'page_title': 'Issue Book to Student'})


@login_required
@teacher_required
def book_return_view(request, pk):
    iss = get_object_or_404(BookIssue, pk=pk)
    if iss.status == BookIssue.Status.ISSUED:
        iss.status = BookIssue.Status.RETURNED
        iss.return_date = timezone.now().date()
        iss.book.available_copies += 1
        iss.book.save()
        iss.save()
        ActivityLog.log_activity(request.user, 'UPDATE', 'Library', f"Returned book '{iss.book.title}' from {iss.student.get_full_name()}", request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Book '{iss.book.title}' marked as RETURNED!")
    return redirect('library:issue_list')
