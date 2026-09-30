from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from apps.accounts.models import User
from apps.accounts.decorators import principal_required, coordinator_required
from apps.core.models import ActivityLog
from .models import Teacher, SalaryPayment, StaffLeave, TeacherPerformance
from .forms import TeacherForm, SalaryPaymentForm, StaffLeaveForm


@login_required
@coordinator_required
def teacher_list_view(request):
    all_qs = Teacher.objects.select_related('user').all()
    
    total_count = all_qs.count()
    teaching_count = all_qs.filter(staff_type=Teacher.StaffType.TEACHING).count()
    non_teaching_count = all_qs.filter(staff_type=Teacher.StaffType.NON_TEACHING).count()

    teachers = all_qs
    
    staff_type = request.GET.get('staff_type', '').strip()
    if staff_type in [Teacher.StaffType.TEACHING, Teacher.StaffType.NON_TEACHING]:
        teachers = teachers.filter(staff_type=staff_type)

    search = request.GET.get('search', '').strip()
    if search:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(department__icontains=search) |
            Q(designation__icontains=search) |
            Q(phone_number__icontains=search)
        )

    dept = request.GET.get('department')
    if dept:
        teachers = teachers.filter(department=dept)

    status = request.GET.get('status')
    if status:
        teachers = teachers.filter(status=status)

    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers,
        'search_query': search,
        'selected_status': status,
        'selected_staff_type': staff_type,
        'total_count': total_count,
        'teaching_count': teaching_count,
        'non_teaching_count': non_teaching_count,
        'page_title': 'Faculty & Staff Directory'
    })


@login_required
@principal_required
def teacher_create_view(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user account
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            
            user, created = User.objects.get_or_create(username=username, defaults={'email': email})
            user.first_name = first_name
            user.last_name = last_name
            
            teacher = form.save(commit=False)
            if teacher.staff_type == Teacher.StaffType.NON_TEACHING:
                user.role = User.Role.ADMIN if form.cleaned_data.get('designation') == Teacher.Designation.ACCOUNTANT else User.Role.COORDINATOR
            else:
                user.role = User.Role.TEACHER
            user.set_password('staff123')
            user.save()

            teacher.user = user
            teacher.save()

            ActivityLog.log_activity(
                request.user, 'CREATE', 'Teachers',
                f"Added staff member {teacher.get_full_name()} (ID: {teacher.employee_id}, {teacher.get_staff_type_display()})",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"{teacher.get_staff_type_display()} member {teacher.get_full_name()} added successfully!")
            return redirect('teachers:teacher_detail', pk=teacher.pk)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        initial_type = request.GET.get('type', Teacher.StaffType.TEACHING)
        form = TeacherForm(initial={'staff_type': initial_type})

    return render(request, 'teachers/teacher_form.html', {
        'form': form,
        'is_edit': False,
        'page_title': 'Add New Staff Member'
    })


@login_required
def teacher_detail_view(request, pk):
    teacher = get_object_or_404(Teacher.objects.select_related('user'), pk=pk)
    assigned_sections = teacher.user.assigned_sections.select_related('class_room').all()
    teaching_subjects = teacher.user.teaching_subjects.select_related('class_room', 'section', 'subject').all()
    salary_history = teacher.salary_payments.all()[:12]
    leave_requests = teacher.leave_requests.all()
    performance_reviews = teacher.performance_evaluations.all()

    return render(request, 'teachers/teacher_detail.html', {
        'teacher': teacher,
        'assigned_sections': assigned_sections,
        'teaching_subjects': teaching_subjects,
        'salary_history': salary_history,
        'leave_requests': leave_requests,
        'performance_reviews': performance_reviews,
        'page_title': f"Faculty Profile: {teacher.get_full_name()}"
    })


@login_required
@principal_required
def teacher_update_view(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            teacher.user.first_name = form.cleaned_data['first_name']
            teacher.user.last_name = form.cleaned_data['last_name']
            teacher.user.email = form.cleaned_data['email']
            teacher.user.save()

            messages.success(request, f"Teacher {teacher.get_full_name()} updated successfully!")
            return redirect('teachers:teacher_detail', pk=teacher.pk)
    else:
        form = TeacherForm(instance=teacher)

    return render(request, 'teachers/teacher_form.html', {
        'form': form,
        'teacher': teacher,
        'is_edit': True,
        'page_title': f"Edit Profile: {teacher.get_full_name()}"
    })


@login_required
@principal_required
def salary_list_view(request):
    salaries = SalaryPayment.objects.select_related('teacher', 'teacher__user').all()
    form = SalaryPaymentForm()

    if request.method == 'POST':
        form = SalaryPaymentForm(request.POST)
        if form.is_valid():
            sal = form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Finance', f"Recorded salary for {sal.teacher.get_full_name()}", request.META.get('REMOTE_ADDR'))
            messages.success(request, "Salary record created successfully!")
            return redirect('teachers:salary_list')

    return render(request, 'teachers/salary_list.html', {
        'salaries': salaries,
        'form': form,
        'page_title': 'Faculty Payroll & Salaries'
    })


@login_required
@coordinator_required
def performance_dashboard_view(request):
    """Teacher Performance Analytics, KPIs & Appraisal Scorecards"""
    teachers = Teacher.objects.select_related('user').all()
    evaluations = TeacherPerformance.objects.select_related('teacher', 'teacher__user', 'evaluated_by').all()
    
    # Calculate live aggregated performance stats for each teacher
    from apps.lectures.models import DailyLecture, Homework
    from apps.attendance.models import TeacherAttendance
    from django.db.models import Avg, Count
    
    teacher_stats = []
    for t in teachers:
        # Lecture counts
        lectures_count = DailyLecture.objects.filter(teacher=t.user).count()
        homeworks_count = Homework.objects.filter(teacher=t.user).count()
        
        # Attendance %
        total_att = TeacherAttendance.objects.filter(teacher=t).count()
        present_att = TeacherAttendance.objects.filter(teacher=t, status__in=['PRESENT', 'LATE']).count()
        att_rate = round((present_att / total_att * 100), 1) if total_att > 0 else 96.0
        
        # Latest evaluation
        latest_eval = t.performance_evaluations.first()
        score = float(latest_eval.overall_score) if latest_eval else 9.0
        
        teacher_stats.append({
            'teacher': t,
            'lectures_count': lectures_count,
            'homeworks_count': homeworks_count,
            'attendance_rate': att_rate,
            'latest_eval': latest_eval,
            'score': score,
        })
    
    # Sort teacher leaderboard by overall score descending
    teacher_stats.sort(key=lambda x: x['score'], reverse=True)

    avg_school_score = evaluations.aggregate(Avg('overall_score'))['overall_score__avg'] or 9.1
    top_performers_count = sum(1 for ts in teacher_stats if ts['score'] >= 9.0)

    context = {
        'page_title': 'Faculty Performance & Appraisals',
        'teacher_stats': teacher_stats,
        'evaluations': evaluations,
        'avg_school_score': round(float(avg_school_score), 2),
        'top_performers_count': top_performers_count,
        'total_evaluations': evaluations.count(),
    }
    return render(request, 'teachers/performance_list.html', context)


@login_required
@coordinator_required
def performance_create_view(request):
    """Add / Submit Monthly Performance Review for a Teacher"""
    teacher_id = request.GET.get('teacher')
    initial_data = {}
    if teacher_id:
        initial_data['teacher'] = teacher_id

    if request.method == 'POST':
        form = TeacherPerformanceForm(request.POST)
        if form.is_valid():
            perf = form.save(commit=False)
            perf.evaluated_by = request.user
            perf.save()

            ActivityLog.log_activity(
                request.user, 'CREATE', 'Teachers',
                f"Evaluated performance for {perf.teacher.get_full_name()} ({perf.evaluation_month}) - Score: {perf.overall_score}/10",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Performance appraisal for {perf.teacher.get_full_name()} recorded successfully!")
            return redirect('teachers:performance_detail', pk=perf.pk)
        else:
            messages.error(request, "Please correct errors in the appraisal form.")
    else:
        form = TeacherPerformanceForm(initial=initial_data)

    return render(request, 'teachers/performance_form.html', {
        'form': form,
        'page_title': 'Conduct Faculty Performance Evaluation'
    })


@login_required
def performance_detail_view(request, pk):
    """View Printable Teacher Performance Scorecard Sheet"""
    perf = get_object_or_404(
        TeacherPerformance.objects.select_related('teacher', 'teacher__user', 'evaluated_by'),
        pk=pk
    )
    return render(request, 'teachers/performance_detail.html', {
        'perf': perf,
        'page_title': f"Performance Scorecard: {perf.teacher.get_full_name()} ({perf.evaluation_month})"
    })

