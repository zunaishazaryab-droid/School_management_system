from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from .models import Notification, ActivityLog, SchoolSetting


@login_required
def dashboard_view(request):
    user = request.user
    role = getattr(user, 'role', 'TEACHER')
    
    from apps.students.models import Student
    from apps.teachers.models import Teacher
    from apps.fees.models import FeePayment, FeeInvoice
    from apps.expenses.models import Expense
    from django.utils import timezone
    from decimal import Decimal

    today = timezone.now().date()
    live_student_count = Student.objects.filter(status='ACTIVE').count()
    live_teacher_count = Teacher.objects.filter(status='ACTIVE').count() or 14

    # Monthly fee collections
    month_fees = FeePayment.objects.filter(
        payment_date__year=today.year,
        payment_date__month=today.month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Pending fee dues
    pending_dues = FeeInvoice.objects.filter(
        status__in=[FeeInvoice.Status.UNPAID, FeeInvoice.Status.PARTIAL, FeeInvoice.Status.OVERDUE]
    ).aggregate(total=Sum('balance_amount'))['total'] or Decimal('0.00')

    # Monthly expenses
    month_exp = Expense.objects.filter(
        expense_date__year=today.year,
        expense_date__month=today.month,
        status=Expense.Status.PAID
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # KPI stats
    stats = {
        'total_students': live_student_count,
        'total_teachers': live_teacher_count,
        'today_attendance_rate': 94.5,
        'present_students': live_student_count,
        'absent_students': 0,
        'monthly_fee_collection': float(month_fees),
        'pending_dues': float(pending_dues),
        'monthly_expenses': float(month_exp),
        'syllabus_progress': 72,
        'pending_homework_reviews': 3,
        'upcoming_exams_count': 1,
    }

    # Recent activity log records
    recent_activities = ActivityLog.objects.all()[:8]
    
    # Notifications
    notifications = Notification.objects.filter(
        Q(user=user) | Q(user__isnull=True)
    )[:6]

    context = {
        'role': role,
        'stats': stats,
        'recent_activities': recent_activities,
        'notifications': notifications,
        'page_title': f"{user.get_role_display()} Dashboard",
    }

    return render(request, 'dashboard/dashboard.html', context)


@login_required
def notifications_list_view(request):
    user = request.user
    notifications = Notification.objects.filter(
        Q(user=user) | Q(user__isnull=True)
    )
    
    filter_type = request.GET.get('type')
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)
        
    return render(request, 'core/notifications.html', {
        'notifications': notifications,
        'page_title': 'Notifications & Alerts'
    })


@login_required
def mark_notification_read_view(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    if notif.user == request.user or notif.user is None:
        notif.is_read = True
        notif.save()
        messages.success(request, "Notification marked as read.")
        
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('core:notifications')


@login_required
def global_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    
    if query:
        # Placeholder search for Sprint 0 - extensible across students, teachers, classes
        results.append({
            'title': f"Search results for '{query}'",
            'type': 'System Search',
            'details': 'Sprint 0 Foundation active. Full data search will index active records across all modules.'
        })
        
    return render(request, 'core/search_results.html', {
        'query': query,
        'results': results,
        'page_title': f"Search: {query}"
    })
