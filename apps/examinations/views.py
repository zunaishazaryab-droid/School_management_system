from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal

from .models import Exam, ExamSchedule, ExamMarks, ExamStudentResult, GradeScale
from .forms import ExamForm, ExamScheduleForm, GradeScaleForm
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject
from apps.students.models import Student
from apps.core.models import ActivityLog


@login_required
def exam_list_view(request):
    """List of all examinations & assessments"""
    exams = Exam.objects.select_related('academic_year').annotate(
        total_papers=Count('schedules', distinct=True),
        total_results=Count('student_results', distinct=True)
    )

    academic_year_id = request.GET.get('academic_year')
    exam_type = request.GET.get('exam_type')

    if academic_year_id:
        exams = exams.filter(academic_year_id=academic_year_id)
    if exam_type:
        exams = exams.filter(exam_type=exam_type)

    academic_years = AcademicYear.objects.all()

    # KPI counts
    total_exams_count = exams.count()
    active_exams_count = exams.filter(is_active=True).count()
    published_count = exams.filter(is_published=True).count()

    context = {
        'page_title': 'Examinations & Results',
        'exams': exams,
        'academic_years': academic_years,
        'academic_year_id': academic_year_id,
        'exam_type': exam_type,
        'total_exams_count': total_exams_count,
        'active_exams_count': active_exams_count,
        'published_count': published_count,
    }
    return render(request, 'examinations/exam_list.html', context)


@login_required
def exam_create_view(request):
    """Create a new examination"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Examinations',
                description=f"Created examination: {exam.title} ({exam.academic_year.name})"
            )
            messages.success(request, f"Examination '{exam.title}' created successfully.")
            return redirect('examinations:exam_detail', pk=exam.pk)
    else:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        form = ExamForm(initial={
            'academic_year': current_year,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date(),
            'is_active': True,
        })

    return render(request, 'examinations/exam_form.html', {
        'form': form,
        'page_title': 'Setup New Examination'
    })


@login_required
def exam_edit_view(request, pk):
    """Edit examination details"""
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, f"Examination '{exam.title}' updated.")
            return redirect('examinations:exam_detail', pk=exam.pk)
    else:
        form = ExamForm(instance=exam)

    return render(request, 'examinations/exam_form.html', {
        'form': form,
        'exam': exam,
        'page_title': f"Edit Examination: {exam.title}"
    })


@login_required
def exam_detail_view(request, pk):
    """Exam Overview, Date Sheet, and Class-wise Marks status"""
    exam = get_object_or_404(Exam.objects.select_related('academic_year'), pk=pk)
    schedules = exam.schedules.select_related('class_room', 'subject').order_by('exam_date', 'start_time')
    classes = ClassRoom.objects.all()

    # Filter schedules by class if chosen
    class_filter = request.GET.get('class_room', '')
    if class_filter:
        schedules = schedules.filter(class_room_id=class_filter)

    # Class-wise result counts
    results_summary = exam.student_results.values('class_room__id', 'class_room__name').annotate(
        total_students=Count('id'),
        passed_students=Count('id', filter=Q(is_passed=True)),
        avg_percentage=Avg('percentage')
    ).order_by('class_room__numeric_level')

    schedule_form = ExamScheduleForm(initial={'exam': exam})

    context = {
        'page_title': exam.title,
        'exam': exam,
        'schedules': schedules,
        'classes': classes,
        'class_filter': class_filter,
        'results_summary': results_summary,
        'schedule_form': schedule_form,
    }
    return render(request, 'examinations/exam_detail.html', context)


@login_required
def exam_schedule_create_view(request, exam_id):
    """Add a paper to the exam date sheet"""
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == 'POST':
        form = ExamScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.exam = exam
            schedule.save()
            messages.success(request, f"Paper for {schedule.subject.name} ({schedule.class_room.name}) added to date sheet.")
        else:
            messages.error(request, "Failed to add paper. Please check that this subject isn't already scheduled for this class.")
    return redirect('examinations:exam_detail', pk=exam.pk)


@login_required
def exam_schedule_delete_view(request, pk):
    """Delete a paper from date sheet"""
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    exam_id = schedule.exam.id
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, "Paper removed from date sheet.")
    return redirect('examinations:exam_detail', pk=exam_id)


@login_required
def exam_marks_entry_view(request, schedule_id):
    """Enter and update subject marks for all students in a class"""
    schedule = get_object_or_404(ExamSchedule.objects.select_related('exam', 'class_room', 'subject'), pk=schedule_id)
    students = Student.objects.filter(current_class=schedule.class_room, status='ACTIVE').select_related('current_section')

    # Get or pre-fetch existing marks
    existing_marks_map = {m.student_id: m for m in schedule.marks_records.all()}

    if request.method == 'POST':
        saved_count = 0
        for st in students:
            marks_val_str = request.POST.get(f'marks_{st.id}', '').strip()
            is_absent = request.POST.get(f'absent_{st.id}') == '1'
            remarks = request.POST.get(f'remarks_{st.id}', '').strip()

            if is_absent:
                marks_obj, created = ExamMarks.objects.update_or_create(
                    exam_schedule=schedule,
                    student=st,
                    defaults={
                        'marks_obtained': Decimal('0.00'),
                        'is_absent': True,
                        'remarks': remarks or 'Absent on exam day',
                        'recorded_by': request.user
                    }
                )
                saved_count += 1
            elif marks_val_str != '':
                try:
                    marks_val = Decimal(marks_val_str)
                    marks_val = min(marks_val, Decimal(str(schedule.total_marks)))
                    marks_obj, created = ExamMarks.objects.update_or_create(
                        exam_schedule=schedule,
                        student=st,
                        defaults={
                            'marks_obtained': marks_val,
                            'is_absent': False,
                            'remarks': remarks,
                            'recorded_by': request.user
                        }
                    )
                    saved_count += 1
                except Exception:
                    pass

        ActivityLog.log_activity(
            user=request.user,
            action='UPDATE',
            module='Examinations',
            description=f"Updated {saved_count} marks records for {schedule.class_room.name} : {schedule.subject.name} ({schedule.exam.title})"
        )

        messages.success(request, f"Saved marks records for {saved_count} students.")
        return redirect('examinations:marks_entry', schedule_id=schedule.id)

    # Prepare student rows with existing marks
    student_rows = []
    for st in students:
        mark_rec = existing_marks_map.get(st.id)
        student_rows.append({
            'student': st,
            'mark_rec': mark_rec,
            'obtained': mark_rec.marks_obtained if mark_rec else '',
            'is_absent': mark_rec.is_absent if mark_rec else False,
            'remarks': mark_rec.remarks if mark_rec else '',
        })

    context = {
        'page_title': f"Marks Entry - {schedule.class_room.name} : {schedule.subject.name}",
        'schedule': schedule,
        'student_rows': student_rows,
    }
    return render(request, 'examinations/marks_entry.html', context)


@login_required
def exam_calculate_results_view(request, exam_id):
    """Compute student overall totals, percentage, grade, and positions"""
    exam = get_object_or_404(Exam, pk=exam_id)
    
    classes = ClassRoom.objects.all()
    calculated_count = 0

    for cl in classes:
        # Get all exam schedules (papers) for this class
        schedules = list(exam.schedules.filter(class_room=cl))
        if not schedules:
            continue

        class_total_max_marks = sum(s.total_marks for s in schedules)
        students = Student.objects.filter(current_class=cl, status='ACTIVE')

        class_results_to_rank = []

        for st in students:
            marks_list = ExamMarks.objects.filter(exam_schedule__in=schedules, student=st)
            
            # Sum of marks obtained
            obtained_sum = sum(m.marks_obtained for m in marks_list if not m.is_absent)
            
            # Check if student failed in any paper
            has_failed_paper = False
            for m in marks_list:
                if m.is_absent or m.marks_obtained < m.exam_schedule.passing_marks:
                    has_failed_paper = True

            pct = (obtained_sum / Decimal(str(class_total_max_marks)) * Decimal('100.00')) if class_total_max_marks > 0 else Decimal('0.00')
            grade, remarks = GradeScale.get_grade_for_percentage(pct)

            is_passed = (not has_failed_paper) and (pct >= Decimal('33.00'))

            res_obj, _ = ExamStudentResult.objects.update_or_create(
                exam=exam,
                student=st,
                defaults={
                    'class_room': cl,
                    'section': st.current_section,
                    'total_marks': Decimal(str(class_total_max_marks)),
                    'obtained_marks': obtained_sum,
                    'percentage': round(pct, 2),
                    'grade': grade,
                    'grade_remarks': remarks,
                    'is_passed': is_passed,
                }
            )
            class_results_to_rank.append(res_obj)
            calculated_count += 1

        # Calculate class and section positions
        # Order by percentage descending
        class_results_to_rank.sort(key=lambda x: x.percentage, reverse=True)
        for rank, res in enumerate(class_results_to_rank, start=1):
            res.position_in_class = rank
            res.save()

        # Group by section for section ranks
        sections = cl.sections.all()
        for sec in sections:
            sec_results = [r for r in class_results_to_rank if r.section_id == sec.id]
            sec_results.sort(key=lambda x: x.percentage, reverse=True)
            for s_rank, s_res in enumerate(sec_results, start=1):
                s_res.position_in_section = s_rank
                s_res.save()

    ActivityLog.log_activity(
        user=request.user,
        action='UPDATE',
        module='Examinations',
        description=f"Calculated and finalized results for {calculated_count} students in {exam.title}."
    )

    messages.success(request, f"Successfully calculated and ranked results for {calculated_count} students across all classes.")
    return redirect('examinations:exam_detail', pk=exam.pk)


@login_required
def exam_class_result_view(request, exam_id, class_id):
    """View class-wise tabulated result gazette"""
    exam = get_object_or_404(Exam, pk=exam_id)
    class_room = get_object_or_404(ClassRoom, pk=class_id)
    
    section_id = request.GET.get('section')
    results = ExamStudentResult.objects.filter(exam=exam, class_room=class_room).select_related('student', 'section')

    if section_id:
        results = results.filter(section_id=section_id)

    results = results.order_by('position_in_section', '-percentage')

    schedules = exam.schedules.filter(class_room=class_room).select_related('subject').order_by('subject__name')
    sections = class_room.sections.all()

    # Pass rate KPI
    total_res = results.count()
    passed_res = results.filter(is_passed=True).count()
    pass_percentage = round((passed_res / total_res * 100), 1) if total_res > 0 else 0

    context = {
        'page_title': f"Result Gazette - {class_room.name} ({exam.title})",
        'exam': exam,
        'class_room': class_room,
        'results': results,
        'schedules': schedules,
        'sections': sections,
        'section_id': section_id,
        'total_res': total_res,
        'passed_res': passed_res,
        'pass_percentage': pass_percentage,
    }
    return render(request, 'examinations/class_result.html', context)


@login_required
def student_report_card_view(request, exam_id, student_id):
    """Printable official report card / result transcript for a student"""
    exam = get_object_or_404(Exam, pk=exam_id)
    student = get_object_or_404(Student.objects.select_related('current_class', 'current_section', 'academic_year'), pk=student_id)
    
    result = ExamStudentResult.objects.filter(exam=exam, student=student).first()
    schedules = exam.schedules.filter(class_room=student.current_class).select_related('subject')

    marks_rows = []
    for sch in schedules:
        m_rec = ExamMarks.objects.filter(exam_schedule=sch, student=student).first()
        obt = m_rec.marks_obtained if m_rec and not m_rec.is_absent else Decimal('0.00')
        is_abs = m_rec.is_absent if m_rec else False
        pct = (obt / Decimal(str(sch.total_marks)) * Decimal('100.00')) if sch.total_marks > 0 else Decimal('0.00')
        sub_grade, sub_rem = GradeScale.get_grade_for_percentage(pct)

        marks_rows.append({
            'subject': sch.subject,
            'total_marks': sch.total_marks,
            'passing_marks': sch.passing_marks,
            'obtained': obt,
            'is_absent': is_abs,
            'percentage': round(pct, 1),
            'grade': sub_grade,
            'remarks': sub_rem if not is_abs else 'Absent',
            'is_pass': (obt >= sch.passing_marks) and not is_abs,
        })

    # Attendance stats for this student
    attendance_count = student.attendance_records.count()
    presents_count = student.attendance_records.filter(status='PRESENT').count()
    attendance_rate = round((presents_count / attendance_count * 100), 1) if attendance_count > 0 else 100.0

    context = {
        'page_title': f"Report Card - {student.get_full_name()} ({exam.title})",
        'exam': exam,
        'student': student,
        'result': result,
        'marks_rows': marks_rows,
        'attendance_count': attendance_count,
        'attendance_rate': attendance_rate,
    }
    return render(request, 'examinations/report_card.html', context)


@login_required
def grading_scale_list_view(request):
    """View and manage grade thresholds"""
    scales = GradeScale.objects.all()
    if request.method == 'POST':
        form = GradeScaleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade scale threshold added.")
            return redirect('examinations:grade_scales')
    else:
        form = GradeScaleForm()

    return render(request, 'examinations/grade_scales.html', {
        'scales': scales,
        'form': form,
        'page_title': 'Grading Scales & GPA Setup'
    })
