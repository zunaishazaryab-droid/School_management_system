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
    teachers = Teacher.objects.select_related('user').all()

    search = request.GET.get('search', '').strip()
    if search:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(department__icontains=search) |
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
            user.role = User.Role.TEACHER
            user.set_password('teacher123')
            user.save()

            teacher = form.save(commit=False)
            teacher.user = user
            teacher.save()

            ActivityLog.log_activity(
                request.user, 'CREATE', 'Teachers',
                f"Added faculty member {teacher.get_full_name()} (ID: {teacher.employee_id})",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Teacher {teacher.get_full_name()} added successfully!")
            return redirect('teachers:teacher_detail', pk=teacher.pk)
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = TeacherForm()

    return render(request, 'teachers/teacher_form.html', {
        'form': form,
        'is_edit': False,
        'page_title': 'Add New Faculty Member'
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
