from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from apps.accounts.models import User
from apps.accounts.decorators import teacher_required, coordinator_required
from apps.core.models import ActivityLog
from apps.academics.models import ClassRoom, Section, AcademicYear
from .models import Student, StudentDocument, StudentPromotionHistory
from .forms import StudentForm, StudentDocumentForm, StudentPromotionForm


def get_or_create_student_user(student):
    """Automatically create or link a student portal User account for the student."""
    if student.user:
        return student.user
    
    base_user = student.admission_number.lower().replace('/', '.').replace('-', '.').replace(' ', '')
    username = base_user
    counter = 1
    while User.objects.filter(username=username).exclude(student_profile=student).exists():
        username = f"{base_user}.{counter}"
        counter += 1

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': student.first_name,
            'last_name': student.last_name,
            'email': student.guardian_email or f"{username}@student.genxvision.edu.pk",
            'role': User.Role.STUDENT,
            'phone_number': student.guardian_phone
        }
    )
    if created:
        user.set_password('student123')
        user.save()
    
    student.user = user
    student.save(update_fields=['user'])
    return user


@login_required
@teacher_required
def student_list_view(request):
    students = Student.objects.select_related('current_class', 'current_section', 'academic_year').all()

    # Search filter
    search_query = request.GET.get('search', '').strip()
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(admission_number__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(guardian_name__icontains=search_query) |
            Q(guardian_phone__icontains=search_query)
        )

    # Class & Section Filters
    class_id = request.GET.get('class_id')
    if class_id:
        students = students.filter(current_class_id=class_id)

    section_id = request.GET.get('section_id')
    if section_id:
        students = students.filter(current_section_id=section_id)

    status = request.GET.get('status')
    if status:
        students = students.filter(status=status)
    else:
        # Default to ACTIVE students unless filtered
        students = students.filter(status='ACTIVE')

    # Pagination
    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    classes = ClassRoom.objects.all()
    sections = Section.objects.all()

    return render(request, 'students/student_list.html', {
        'page_obj': page_obj,
        'students_count': students.count(),
        'classes': classes,
        'sections': sections,
        'search_query': search_query,
        'selected_class': int(class_id) if class_id else None,
        'selected_section': int(section_id) if section_id else None,
        'selected_status': status or 'ACTIVE',
        'page_title': 'Students Directory'
    })


@login_required
@coordinator_required
def student_create_view(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            get_or_create_student_user(student)
            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Students',
                description=f"Admitted new student {student.get_full_name()} (ID: {student.admission_number}) in {student.current_class.name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Student {student.get_full_name()} admitted successfully with automated student portal account!")
            return redirect('students:student_detail', pk=student.pk)
        else:
            messages.error(request, "Please correct the errors in the admission form.")
    else:
        # Initial active academic year
        active_year = AcademicYear.objects.filter(is_current=True).first()
        initial_data = {'academic_year': active_year} if active_year else {}
        form = StudentForm(initial=initial_data)

    return render(request, 'students/student_form.html', {
        'form': form,
        'is_edit': False,
        'page_title': 'New Student Admission'
    })


@login_required
@coordinator_required
def student_update_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            student = form.save()
            ActivityLog.log_activity(
                user=request.user,
                action='UPDATE',
                module='Students',
                description=f"Updated profile for student {student.get_full_name()} (ID: {student.admission_number}).",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Student {student.get_full_name()} updated successfully!")
            return redirect('students:student_detail', pk=student.pk)
        else:
            messages.error(request, "Please fix the validation errors below.")
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {
        'form': form,
        'student': student,
        'is_edit': True,
        'page_title': f"Edit Student: {student.get_full_name()}"
    })


@login_required
@teacher_required
def student_detail_view(request, pk):
    student = get_object_or_404(
        Student.objects.select_related('current_class', 'current_section', 'academic_year'),
        pk=pk
    )
    documents = student.documents.all()
    promotion_records = student.promotion_history.select_related('from_class', 'to_class', 'academic_year', 'promoted_by').all()
    doc_form = StudentDocumentForm()

    # Document upload submission
    if request.method == 'POST' and 'upload_document' in request.POST:
        doc_form = StudentDocumentForm(request.POST, request.FILES)
        if doc_form.is_valid():
            doc = doc_form.save(commit=False)
            doc.student = student
            doc.save()
            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Students',
                description=f"Uploaded document '{doc.title}' for student {student.get_full_name()}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Document '{doc.title}' uploaded successfully!")
            return redirect('students:student_detail', pk=student.pk)

    return render(request, 'students/student_detail.html', {
        'student': student,
        'documents': documents,
        'promotion_records': promotion_records,
        'doc_form': doc_form,
        'page_title': f"Student Profile: {student.get_full_name()}"
    })


@login_required
@teacher_required
def student_card_view(request, pk):
    """Printable Student Identity Card & Profile Sheet"""
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'students/student_card.html', {
        'student': student,
        'page_title': f"Student ID Card — {student.get_full_name()}"
    })


@login_required
@coordinator_required
def student_promotion_view(request):
    classes = ClassRoom.objects.all()
    academic_years = AcademicYear.objects.all()

    if request.method == 'POST':
        form = StudentPromotionForm(request.POST)
        if form.is_valid():
            from_class = form.cleaned_data['from_class']
            from_section = form.cleaned_data['from_section']
            to_class = form.cleaned_data['to_class']
            to_section = form.cleaned_data['to_section']
            target_year = form.cleaned_data['target_academic_year']
            remarks = form.cleaned_data['remarks']
            selected_student_ids = request.POST.getlist('selected_students')

            if not selected_student_ids:
                messages.warning(request, "Please select at least one student to promote.")
            else:
                students_to_promote = Student.objects.filter(id__in=selected_student_ids)
                count = 0
                for st in students_to_promote:
                    # Save promotion history
                    StudentPromotionHistory.objects.create(
                        student=st,
                        from_class=st.current_class,
                        from_section=st.current_section,
                        to_class=to_class,
                        to_section=to_section,
                        academic_year=target_year,
                        promoted_by=request.user,
                        remarks=remarks
                    )
                    # Update student placement
                    st.current_class = to_class
                    st.current_section = to_section
                    st.academic_year = target_year
                    st.save()
                    count += 1

                ActivityLog.log_activity(
                    user=request.user,
                    action='UPDATE',
                    module='Students',
                    description=f"Promoted {count} students from {from_class.name} to {to_class.name}.",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                messages.success(request, f"Successfully promoted {count} students to {to_class.name} - Section {to_section.name}!")
                return redirect('students:student_list')
    else:
        form = StudentPromotionForm()

    return render(request, 'students/student_promotion.html', {
        'form': form,
        'classes': classes,
        'academic_years': academic_years,
        'page_title': 'Student Promotion Workflow'
    })


@login_required
@coordinator_required
def student_delete_view(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.get_full_name()
        adm = student.admission_number
        student.delete()
        ActivityLog.log_activity(
            user=request.user,
            action='DELETE',
            module='Students',
            description=f"Deleted student record for {name} (ID: {adm}).",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Student {name} deleted successfully.")
        return redirect('students:student_list')
    return redirect('students:student_detail', pk=pk)


@login_required
def parent_portal_view(request):
    """Unified Student & Parent Portal with live attendance, fees, homework & result card"""
    from apps.attendance.models import StudentAttendance
    from apps.lectures.models import Homework
    from apps.fees.models import FeeInvoice
    from apps.examinations.models import ExamStudentResult
    from django.db.models import Sum

    all_students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section')
    student_id = request.GET.get('student_id')
    query = request.GET.get('q', '').strip()

    selected_student = None
    if student_id:
        selected_student = all_students.filter(id=student_id).first()
    elif query:
        selected_student = all_students.filter(
            Q(admission_number__icontains=query) |
            Q(guardian_phone__icontains=query) |
            Q(first_name__icontains=query)
        ).first()
    else:
        selected_student = all_students.first()

    attendance_rate = 95.0
    pending_fees = 0.0
    recent_homework = []
    student_invoices = []
    latest_result = None

    if selected_student:
        # Attendance calculation
        total_att = StudentAttendance.objects.filter(student=selected_student).count()
        present_att = StudentAttendance.objects.filter(student=selected_student, status__in=['PRESENT', 'LATE']).count()
        attendance_rate = round((present_att / total_att * 100), 1) if total_att > 0 else 94.5

        # Fee Dues
        pending_fees = FeeInvoice.objects.filter(
            student=selected_student,
            status__in=[FeeInvoice.Status.UNPAID, FeeInvoice.Status.PARTIAL, FeeInvoice.Status.OVERDUE]
        ).aggregate(total=Sum('balance_amount'))['total'] or 0.0

        # Invoices
        student_invoices = FeeInvoice.objects.filter(student=selected_student)[:6]

        # Recent Homework
        recent_homework = Homework.objects.filter(
            class_room=selected_student.current_class,
            section=selected_student.current_section
        )[:6]

        # Latest Exam Result
        latest_result = ExamStudentResult.objects.filter(student=selected_student).first()

    context = {
        'page_title': 'Student & Parent Academic Portal',
        'all_students': all_students,
        'selected_student': selected_student,
        'attendance_rate': attendance_rate,
        'pending_fees': float(pending_fees),
        'recent_homework': recent_homework,
        'student_invoices': student_invoices,
        'latest_result': latest_result,
        'search_query': query,
    }
    return render(request, 'students/parent_portal.html', context)


@login_required
@coordinator_required
def student_batch_id_cards_view(request):
    """Batch print PVC Student ID cards for class cohorts"""
    classes = ClassRoom.objects.all()
    class_id = request.GET.get('class_id')

    students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section', 'academic_year')
    if class_id:
        students = students.filter(current_class_id=class_id)

    return render(request, 'students/student_batch_id_cards.html', {
        'classes': classes,
        'students': students,
        'selected_class': class_id,
        'page_title': 'Batch Student PVC ID Card Printing'
    })


@login_required
@teacher_required
def student_certificate_view(request, pk):
    """Generate official School Leaving (SLC), Character & Bonafide Certificates"""
    student = get_object_or_404(
        Student.objects.select_related('current_class', 'current_section', 'academic_year'),
        pk=pk
    )
    cert_type = request.GET.get('type', 'SLC').upper()

    ActivityLog.log_activity(
        user=request.user,
        action='PRINT',
        module='Students',
        description=f"Generated {cert_type} certificate for {student.get_full_name()} ({student.admission_number}).",
        ip_address=request.META.get('REMOTE_ADDR')
    )

    return render(request, 'students/student_certificate.html', {
        'student': student,
        'cert_type': cert_type,
        'today': timezone.now().date(),
        'page_title': f"{cert_type} Certificate: {student.get_full_name()}"
    })


@login_required
def student_dashboard_view(request, pk=None):
    """
    Dedicated Student Dashboard:
    Automatically fetches and displays ALL personal academic data for the target student
    (Live Attendance, Fee Challans & Balance, Class Timetable, Daily Homework, Exam Results, Syllabus, Lectures & Notices).
    """
    from apps.attendance.models import StudentAttendance
    from apps.lectures.models import Homework, DailyLecture
    from apps.syllabus.models import SyllabusChapter
    from apps.fees.models import FeeInvoice
    from apps.examinations.models import ExamStudentResult, OnlineAssessment, ExamMarks, Exam
    from apps.academics.models import TimetableEntry, Period
    from apps.communication.models import Announcement
    from django.db.models import Sum

    student = None
    all_students = []

    # 1. Determine target student
    if getattr(request.user, 'is_student', False) and hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
    elif getattr(request.user, 'is_parent', False):
        student = getattr(request.user, 'student_profile', None) or Student.objects.filter(guardian_phone=request.user.phone_number).first()
    
    if not student:
        if pk:
            student = get_object_or_404(Student.objects.select_related('current_class', 'current_section', 'academic_year'), pk=pk)
        else:
            student_id = request.GET.get('student_id')
            if student_id:
                student = Student.objects.filter(pk=student_id).select_related('current_class', 'current_section', 'academic_year').first()
            elif hasattr(request.user, 'student_profile'):
                student = request.user.student_profile
            else:
                student = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section', 'academic_year').first()

    # For staff/coordinators/principals: list all students to allow switching
    if not getattr(request.user, 'is_student', False):
        all_students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section')

    if not student:
        messages.warning(request, "No active student record found.")
        return redirect('students:student_list')

    # Ensure student has a login user account
    if not student.user:
        get_or_create_student_user(student)

    today = timezone.now().date()
    today_name = timezone.now().strftime('%A')
    today_upper = today_name.upper()

    # 2. Attendance Stats
    attendance_qs = StudentAttendance.objects.filter(student=student)
    total_days = attendance_qs.count()
    present_days = attendance_qs.filter(status='PRESENT').count()
    late_days = attendance_qs.filter(status='LATE').count()
    absent_days = attendance_qs.filter(status='ABSENT').count()
    attendance_rate = round(((present_days + late_days) / total_days * 100), 1) if total_days > 0 else 95.0
    recent_attendance = attendance_qs.order_by('-date')[:7]

    # 3. Fees & Invoices
    student_invoices = FeeInvoice.objects.filter(student=student).order_by('-issue_date')
    fee_agg = student_invoices.aggregate(
        total_billed=Sum('payable_amount'),
        total_paid=Sum('paid_amount'),
        total_balance=Sum('balance_amount')
    )
    total_billed = fee_agg['total_billed'] or 0
    total_paid = fee_agg['total_paid'] or 0
    total_balance = fee_agg['total_balance'] or 0
    latest_invoice = student_invoices.first()

    # 4. Class Timetable (Today & Full Week)
    timetable_qs = TimetableEntry.objects.filter(
        class_room=student.current_class,
        section=student.current_section
    ).select_related('period', 'subject', 'teacher').order_by('day_of_week', 'period__period_number')
    
    today_periods = [p for p in timetable_qs if p.day_of_week == today_upper]

    # 5. Active & Recent Homework
    homework_list = Homework.objects.filter(
        class_room=student.current_class,
        section=student.current_section
    ).select_related('subject', 'teacher').order_by('-assigned_date')[:8]

    # 6. Daily Class Lectures & Diary
    recent_lectures = DailyLecture.objects.filter(
        class_room=student.current_class,
        section=student.current_section
    ).select_related('subject', 'teacher').order_by('-date')[:6]

    # 7. Examination Results & CBT Assessments
    exam_marks_list = ExamMarks.objects.filter(
        student=student
    ).select_related('exam_schedule', 'exam_schedule__subject', 'exam_schedule__exam').order_by('-exam_schedule__exam_date')
    
    exam_results = ExamStudentResult.objects.filter(
        student=student
    ).select_related('exam', 'class_room', 'section').order_by('-exam__start_date')
    
    latest_exam = Exam.objects.filter(is_published=True).first() or Exam.objects.first()

    cbt_exams = OnlineAssessment.objects.filter(
        class_room=student.current_class,
        status=OnlineAssessment.Status.PUBLISHED
    ).order_by('-created_at')[:4]

    # 8. Syllabus Progress
    syllabus_items = SyllabusChapter.objects.filter(
        class_room=student.current_class
    ).select_related('subject')[:6]

    # 9. School Announcements
    announcements = Announcement.objects.filter(
        is_published=True,
        publish_date__lte=today
    ).filter(
        Q(audience__in=['ALL', 'STUDENTS', 'PARENTS']) | Q(audience__isnull=True)
    ).order_by('-publish_date')[:4]

    context = {
        'student': student,
        'all_students': all_students,
        'today_name': today_name,
        'today_date': today,
        
        # Attendance
        'attendance_rate': attendance_rate,
        'total_days': total_days,
        'present_days': present_days,
        'late_days': late_days,
        'absent_days': absent_days,
        'recent_attendance': recent_attendance,
        
        # Fees
        'student_invoices': student_invoices,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'total_balance': total_balance,
        'latest_invoice': latest_invoice,
        
        # Academics
        'timetable_qs': timetable_qs,
        'today_periods': today_periods,
        'homework_list': homework_list,
        'recent_lectures': recent_lectures,
        'exam_results': exam_results,
        'exam_marks_list': exam_marks_list,
        'latest_exam': latest_exam,
        'cbt_exams': cbt_exams,
        'syllabus_items': syllabus_items,
        'announcements': announcements,
        
        'page_title': f"Student Dashboard — {student.get_full_name()} ({student.admission_number})"
    }
    return render(request, 'students/student_dashboard.html', context)


