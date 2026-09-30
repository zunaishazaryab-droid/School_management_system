import os
import io
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from django.http import HttpResponse, FileResponse, Http404
from django.core.paginator import Paginator
from django.conf import settings
from django.core import serializers

from apps.accounts.decorators import admin_required, principal_required, coordinator_required
from apps.accounts.models import User
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academics.models import ClassRoom, Section
from apps.fees.models import FeePayment, FeeInvoice
from apps.expenses.models import Expense
from apps.communication.models import Announcement
from .models import Notification, ActivityLog, SchoolSetting
from .forms import SchoolSettingForm, SystemUserForm


@login_required
def dashboard_view(request):
    user = request.user
    role = getattr(user, 'role', 'TEACHER')
    today = timezone.now().date()
    
    live_student_count = Student.objects.filter(status='ACTIVE').count()
    teaching_count = Teacher.objects.filter(status='ACTIVE', staff_type=Teacher.StaffType.TEACHING).count()
    non_teaching_count = Teacher.objects.filter(status='ACTIVE', staff_type=Teacher.StaffType.NON_TEACHING).count()
    total_staff_count = Teacher.objects.filter(status='ACTIVE').count()

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
        'total_teachers': teaching_count,
        'teaching_staff': teaching_count,
        'non_teaching_staff': non_teaching_count,
        'total_staff': total_staff_count,
        'today_attendance_rate': 94.5,
        'present_students': live_student_count,
        'absent_students': 0,
        'monthly_fee_collection': float(month_fees),
        'pending_dues': float(pending_dues),
        'monthly_expenses': float(month_exp),
        'syllabus_progress': 74,
        'pending_homework_reviews': 3,
        'upcoming_exams_count': 1,
    }

    # Recent activity log records
    recent_activities = ActivityLog.objects.all()[:8]
    
    # Notifications
    notifications = Notification.objects.filter(
        Q(user=user) | Q(user__isnull=True)
    )[:6]

    # Active Circulars for Dashboard
    active_announcements = Announcement.objects.filter(
        is_published=True,
        publish_date__lte=today
    ).filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))[:4]

    context = {
        'role': role,
        'stats': stats,
        'recent_activities': recent_activities,
        'notifications': notifications,
        'active_announcements': active_announcements,
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
        'selected_type': filter_type,
        'page_title': 'Notifications & System Alerts'
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
def mark_all_notifications_read_view(request):
    Notification.objects.filter(
        Q(user=request.user) | Q(user__isnull=True),
        is_read=False
    ).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('core:notifications')


@login_required
def global_search_view(request):
    """Multi-entity live database search"""
    query = request.GET.get('q', '').strip()
    
    student_results = []
    teacher_results = []
    class_results = []
    invoice_results = []
    notice_results = []

    if query:
        # Search Students
        student_results = Student.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(guardian_name__icontains=query) |
            Q(guardian_phone__icontains=query) |
            Q(current_class__name__icontains=query)
        ).select_related('current_class', 'current_section')[:10]

        # Search Teachers
        teacher_results = Teacher.objects.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(employee_id__icontains=query) |
            Q(phone_number__icontains=query) |
            Q(department__icontains=query)
        ).select_related('user')[:10]

        # Search Classes & Sections
        class_results = ClassRoom.objects.filter(
            Q(name__icontains=query)
        )[:6]

        # Search Invoices & Payments
        invoice_results = FeeInvoice.objects.filter(
            Q(invoice_number__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__admission_number__icontains=query)
        ).select_related('student', 'class_room')[:8]

        # Search Announcements
        notice_results = Announcement.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )[:6]

    total_matches = len(student_results) + len(teacher_results) + len(class_results) + len(invoice_results) + len(notice_results)

    return render(request, 'core/search_results.html', {
        'query': query,
        'student_results': student_results,
        'teacher_results': teacher_results,
        'class_results': class_results,
        'invoice_results': invoice_results,
        'notice_results': notice_results,
        'total_matches': total_matches,
        'page_title': f"Search: '{query}'" if query else "Global System Search"
    })


@login_required
@principal_required
def activity_logs_view(request):
    """Audit trail & historical user activity viewer"""
    logs = ActivityLog.objects.select_related('user').all()

    action_filter = request.GET.get('action', '').strip()
    module_filter = request.GET.get('module', '').strip()
    user_filter = request.GET.get('user', '').strip()
    search_query = request.GET.get('q', '').strip()

    if action_filter:
        logs = logs.filter(action=action_filter)
    if module_filter:
        logs = logs.filter(module__iexact=module_filter)
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    if search_query:
        logs = logs.filter(Q(description__icontains=search_query) | Q(ip_address__icontains=search_query))

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    users = User.objects.filter(is_active=True).order_by('username')
    modules = ['Accounts', 'Students', 'Teachers', 'Academics', 'Attendance', 'Lectures', 'Syllabus', 'Fees', 'Examinations', 'Expenses', 'Communication', 'Settings']

    return render(request, 'core/activity_logs.html', {
        'page_obj': page_obj,
        'users': users,
        'modules': modules,
        'action_filter': action_filter,
        'module_filter': module_filter,
        'user_filter': user_filter,
        'search_query': search_query,
        'page_title': 'System Activity Log & Audit Trail'
    })


@login_required
@admin_required
def school_settings_view(request):
    """Update School Branding, Session & Configuration"""
    settings_obj = SchoolSetting.get_settings()

    if request.method == 'POST':
        form = SchoolSettingForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            ActivityLog.log_activity(
                request.user, 'UPDATE', 'Settings',
                f"Updated school general settings and profile: {settings_obj.school_name}",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, "School settings updated successfully!")
            return redirect('core:school_settings')
        else:
            messages.error(request, "Please correct the errors in the settings form.")
    else:
        form = SchoolSettingForm(instance=settings_obj)

    return render(request, 'core/school_settings.html', {
        'form': form,
        'settings_obj': settings_obj,
        'page_title': 'School Profile & General Settings'
    })


@login_required
@admin_required
def user_management_view(request):
    """View and manage system staff users, credentials, and roles"""
    users = User.objects.all().order_by('-date_joined')
    role_filter = request.GET.get('role', '')

    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'core/user_management.html', {
        'users': users,
        'role_filter': role_filter,
        'roles': User.Role.choices,
        'page_title': 'Staff Users & Role Management'
    })


@login_required
@admin_required
def user_create_view(request):
    """Add a new staff login user account"""
    if request.method == 'POST':
        form = SystemUserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            ActivityLog.log_activity(
                request.user, 'CREATE', 'Accounts',
                f"Created user account '{new_user.username}' with role {new_user.get_role_display()}",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"User account '{new_user.username}' created successfully!")
            return redirect('core:user_management')
        else:
            messages.error(request, "Please fix form errors below.")
    else:
        form = SystemUserForm()

    return render(request, 'core/user_form.html', {
        'form': form,
        'page_title': 'Create New Staff Account'
    })


@login_required
@admin_required
def user_toggle_status_view(request, pk):
    """Toggle user active / suspended status"""
    target_user = get_object_or_404(User, pk=pk)
    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own administrative account.")
        return redirect('core:user_management')

    target_user.is_active = not target_user.is_active
    target_user.save()
    status_str = "Activated" if target_user.is_active else "Suspended"
    
    ActivityLog.log_activity(
        request.user, 'UPDATE', 'Accounts',
        f"{status_str} account for {target_user.username}",
        request.META.get('REMOTE_ADDR')
    )
    messages.success(request, f"User account '{target_user.username}' has been {status_str.lower()}.")
    return redirect('core:user_management')


@login_required
@admin_required
def database_backup_view(request):
    """Database backup trigger & export center"""
    db_path = settings.DATABASES['default']['NAME']
    db_size = "N/A"
    if os.path.exists(db_path):
        db_size = f"{round(os.path.getsize(db_path) / 1024, 1)} KB"

    return render(request, 'core/database_backup.html', {
        'db_size': db_size,
        'db_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'page_title': 'Database Backup & System Recovery'
    })


@login_required
@admin_required
def database_download_view(request):
    """Directly download SQLite database or JSON dump file"""
    backup_format = request.GET.get('format', 'sqlite')

    ActivityLog.log_activity(
        request.user, 'BACKUP', 'Settings',
        f"Downloaded database backup snapshot (format: {backup_format})",
        request.META.get('REMOTE_ADDR')
    )

    if backup_format == 'sqlite':
        db_path = settings.DATABASES['default']['NAME']
        if os.path.exists(db_path):
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            response = FileResponse(open(db_path, 'rb'), content_type='application/x-sqlite3')
            response['Content-Disposition'] = f'attachment; filename="school_db_backup_{timestamp}.sqlite3"'
            return response
        else:
            raise Http404("Database file not found.")
    else:
        # JSON Data Dump
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        data = serializers.serialize("json", Student.objects.all(), indent=2)
        response = HttpResponse(data, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="school_data_dump_{timestamp}.json"'
        return response


from .models import Branch


@login_required
@admin_required
def campus_list_view(request):
    """Multi-campus and branch management hub."""
    branches = Branch.objects.all()
    if not branches.exists():
        Branch.objects.create(
            name="Main Campus (Johar Town)",
            code="GXV-MC01",
            campus_type=Branch.CampusType.MAIN,
            address="Plot 14-B, Main Boulevard, Johar Town",
            city="Lahore",
            phone="+92 42 35291001",
            email="main@genxvision.edu.pk",
            principal_name="Prof. Dr. Tariq Mahmood",
            is_main_branch=True,
            is_active=True
        )
        Branch.objects.create(
            name="Junior & Primary Wing",
            code="GXV-JW02",
            campus_type=Branch.CampusType.JUNIOR,
            address="Street 4, Phase 2, Johar Town",
            city="Lahore",
            phone="+92 42 35291002",
            email="junior@genxvision.edu.pk",
            principal_name="Mrs. Ayesha Malik",
            is_main_branch=False,
            is_active=True
        )
        branches = Branch.objects.all()

    if request.method == 'POST' and 'create_branch' in request.POST:
        name = request.POST.get('name')
        code = request.POST.get('code')
        ctype = request.POST.get('campus_type', Branch.CampusType.MAIN)
        addr = request.POST.get('address', '')
        city = request.POST.get('city', 'Lahore')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        pname = request.POST.get('principal_name', '')

        Branch.objects.create(
            name=name, code=code, campus_type=ctype, address=addr, city=city,
            phone=phone, email=email, principal_name=pname, is_active=True
        )
        messages.success(request, f"New Campus '{name}' created successfully!")
        return redirect('core:campus_list')

    active_branch_id = request.session.get('active_branch_id')
    active_branch = Branch.objects.filter(id=active_branch_id).first() if active_branch_id else branches.filter(is_main_branch=True).first()

    return render(request, 'core/campus_list.html', {
        'branches': branches,
        'active_branch': active_branch,
        'page_title': 'Multi-Campus & Branch Management'
    })


@login_required
def switch_campus_view(request, branch_id):
    """Switch active working branch in current session."""
    branch = get_object_or_404(Branch, id=branch_id)
    request.session['active_branch_id'] = branch.id
    request.session['active_branch_name'] = branch.name
    messages.success(request, f"Switched working campus context to: '{branch.name}'")
    return redirect(request.META.get('HTTP_REFERER', 'core:dashboard'))


def verify_badge_view(request, token):
    """Public / Gatekeeper verification portal for QR security badges."""
    # Lookup by admission number or roll number or teacher employee ID
    student = Student.objects.filter(
        Q(admission_number__iexact=token) | Q(roll_number__iexact=token)
    ).select_related('current_class', 'current_section').first()

    teacher = None
    if not student:
        teacher = Teacher.objects.filter(
            Q(employee_id__iexact=token) | Q(user__username__iexact=token)
        ).select_related('user').first()

    is_verified = (student is not None or teacher is not None)

    return render(request, 'core/verify_badge.html', {
        'token': token,
        'is_verified': is_verified,
        'student': student,
        'teacher': teacher,
        'verified_at': timezone.now(),
        'page_title': f"Identity Badge Verification - {token}"
    })


@login_required
def badge_scanner_view(request):
    """Interactive gatekeeper scanner interface for camera / manual barcode scan."""
    return render(request, 'core/badge_scanner.html', {
        'page_title': 'Security Gatekeeper QR & Barcode Scanner'
    })

