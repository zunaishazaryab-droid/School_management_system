from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from apps.accounts.decorators import teacher_required, coordinator_required
from apps.core.models import ActivityLog
from apps.academics.models import ClassRoom, Section, AcademicYear
from .models import Student, StudentDocument, StudentPromotionHistory
from .forms import StudentForm, StudentDocumentForm, StudentPromotionForm


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
            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Students',
                description=f"Admitted new student {student.get_full_name()} (ID: {student.admission_number}) in {student.current_class.name}.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Student {student.get_full_name()} admitted successfully!")
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
