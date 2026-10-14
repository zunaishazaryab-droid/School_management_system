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
from apps.accounts.decorators import teacher_required, admin_required, principal_required


@login_required
def exam_list_view(request):
    """List of all examinations & assessments or student's own exam results"""
    if getattr(request.user, 'is_student', False):
        student = getattr(request.user, 'student_profile', None)
        if not student:
            student = Student.objects.filter(user=request.user).first()

        results = []
        weekly_results = []
        monthly_results = []
        term_results = []
        monthly_groups = []

        if student:
            raw_results = list(ExamStudentResult.objects.filter(student=student).select_related(
                'exam', 'exam__academic_year', 'class_room', 'section'
            ))

            # Fetch all subject marks records for this student
            exam_marks_qs = ExamMarks.objects.filter(student=student).select_related(
                'exam_schedule', 'exam_schedule__subject', 'exam_schedule__exam'
            )
            exam_marks_map = {}
            for m in exam_marks_qs:
                eid = m.exam_schedule.exam_id
                if eid not in exam_marks_map:
                    exam_marks_map[eid] = []
                exam_marks_map[eid].append({
                    'subject_name': m.exam_schedule.subject.name,
                    'marks_obtained': m.marks_obtained,
                    'total_marks': m.exam_schedule.total_marks,
                    'percentage': m.percentage,
                    'is_absent': m.is_absent,
                    'remarks': m.remarks,
                })

            for r in raw_results:
                r.subject_breakdown = exam_marks_map.get(r.exam_id, [])
                r.month_name = r.exam.start_date.strftime('%B %Y') if r.exam.start_date else 'Academic Year'
                r.month_code = r.exam.start_date.strftime('%Y_%m') if r.exam.start_date else 'other'

            # Sort strictly chronologically by start_date so Weekly Test 1, 2, 3... are strictly in sequence!
            results = sorted(raw_results, key=lambda r: r.exam.start_date)

            weekly_results = [r for r in results if r.exam.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.QUIZ_UNIT]]
            monthly_results = [r for r in results if r.exam.exam_type == Exam.ExamType.MONTHLY_TEST]
            term_results = [r for r in results if r.exam.exam_type in [
                Exam.ExamType.FIRST_TERM, Exam.ExamType.SECOND_TERM, Exam.ExamType.MID_TERM, Exam.ExamType.FINAL_TERM
            ]]

            # Group assessments month by month
            seen_months = {}
            for r in results:
                m_key = r.month_name
                if m_key not in seen_months:
                    seen_months[m_key] = {
                        'month_name': m_key,
                        'month_code': r.month_code,
                        'results': [],
                        'weekly_count': 0,
                        'monthly_count': 0,
                        'term_count': 0,
                        'avg_pct': 0,
                    }
                    monthly_groups.append(seen_months[m_key])
                seen_months[m_key]['results'].append(r)
                if r.exam.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.QUIZ_UNIT]:
                    seen_months[m_key]['weekly_count'] += 1
                elif r.exam.exam_type == Exam.ExamType.MONTHLY_TEST:
                    seen_months[m_key]['monthly_count'] += 1
                else:
                    seen_months[m_key]['term_count'] += 1

            for grp in monthly_groups:
                grp_res = grp['results']
                grp['avg_pct'] = round(sum(r.percentage for r in grp_res) / len(grp_res), 1) if grp_res else 0

        total_results_count = len(results)
        passed_results_count = sum(1 for r in results if r.is_passed)
        avg_pct = round(sum(r.percentage for r in results) / total_results_count, 1) if total_results_count > 0 else 0

        weekly_avg = round(sum(r.percentage for r in weekly_results) / len(weekly_results), 1) if weekly_results else 0
        monthly_avg = round(sum(r.percentage for r in monthly_results) / len(monthly_results), 1) if monthly_results else 0
        term_avg = round(sum(r.percentage for r in term_results) / len(term_results), 1) if term_results else 0

        yearly_total_marks = sum(r.total_marks for r in results)
        yearly_obtained_marks = sum(r.obtained_marks for r in results)
        yearly_overall_pct = round((yearly_obtained_marks / yearly_total_marks) * 100, 2) if yearly_total_marks > 0 else 0
        yearly_grade, yearly_remarks = GradeScale.get_grade_for_percentage(yearly_overall_pct)
        final_result = next((r for r in results if r.exam.exam_type == Exam.ExamType.FINAL_TERM), None)
        is_promoted = bool(yearly_overall_pct >= 40 and passed_results_count == total_results_count)

        context = {
            'page_title': 'Annual Academic Assessment & Results',
            'student': student,
            'results': results,
            'monthly_groups': monthly_groups,
            'weekly_results': weekly_results,
            'monthly_results': monthly_results,
            'term_results': term_results,
            'final_result': final_result,
            'total_results_count': total_results_count,
            'passed_results_count': passed_results_count,
            'avg_pct': avg_pct,
            'weekly_avg': weekly_avg,
            'monthly_avg': monthly_avg,
            'term_avg': term_avg,
            'yearly_total_marks': yearly_total_marks,
            'yearly_obtained_marks': yearly_obtained_marks,
            'yearly_overall_pct': yearly_overall_pct,
            'yearly_grade': yearly_grade,
            'yearly_remarks': yearly_remarks,
            'is_promoted': is_promoted,
            'is_student_view': True,
        }
        return render(request, 'examinations/student_results_list.html', context)

    all_exams = Exam.objects.all()
    weekly_count = all_exams.filter(exam_type=Exam.ExamType.WEEKLY_TEST).count()
    monthly_count = all_exams.filter(exam_type=Exam.ExamType.MONTHLY_TEST).count()
    term_count = all_exams.filter(exam_type__in=[
        Exam.ExamType.FIRST_TERM, Exam.ExamType.SECOND_TERM, Exam.ExamType.MID_TERM, Exam.ExamType.FINAL_TERM
    ]).count()

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

    context = {
        'page_title': 'Examinations & Assessment Plan',
        'exams': exams,
        'academic_years': academic_years,
        'academic_year_id': academic_year_id,
        'exam_type': exam_type,
        'total_exams_count': all_exams.count(),
        'weekly_count': weekly_count,
        'monthly_count': monthly_count,
        'term_count': term_count,
        'filtered_count': exams.count(),
    }
    return render(request, 'examinations/exam_list.html', context)


@login_required
@teacher_required
def exam_create_view(request):
    """Create a new examination or test (Weekly, Monthly, Term, etc.)"""
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Examinations',
                description=f"Created assessment: {exam.title} ({exam.academic_year.name})"
            )
            messages.success(request, f"Assessment '{exam.title}' created successfully.")
            return redirect('examinations:exam_detail', pk=exam.pk)
    else:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        initial = {
            'academic_year': current_year,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date(),
            'is_active': True,
        }
        if request.GET.get('type'):
            initial['exam_type'] = request.GET.get('type')
        form = ExamForm(initial=initial)

    return render(request, 'examinations/exam_form.html', {
        'form': form,
        'page_title': 'Setup Assessment / Examination'
    })


@login_required
@teacher_required
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
@teacher_required
def exam_delete_view(request, pk):
    """Delete an examination or test"""
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == 'POST':
        title = exam.title
        exam.delete()
        ActivityLog.log_activity(
            user=request.user,
            action='DELETE',
            module='Examinations',
            description=f"Deleted assessment '{title}'"
        )
        messages.success(request, f"Assessment '{title}' deleted.")
        return redirect('examinations:exam_list')
    return redirect('examinations:exam_detail', pk=pk)


@login_required
@teacher_required
def exam_toggle_publish_view(request, pk):
    """Publish / Unpublish exam results to students and parents"""
    exam = get_object_or_404(Exam, pk=pk)
    exam.is_published = not exam.is_published
    exam.save()
    status_str = "Published to student & parent dashboards" if exam.is_published else "Unpublished (hidden from students)"
    messages.success(request, f"Results for '{exam.title}' are now {status_str}.")
    return redirect('examinations:exam_detail', pk=pk)



@login_required
def exam_detail_view(request, pk):
    """Exam Overview, Date Sheet, and Class-wise Marks status"""
    if getattr(request.user, 'is_student', False):
        return redirect('examinations:exam_list')

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
@teacher_required
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
@teacher_required
def exam_schedule_delete_view(request, pk):
    """Delete a paper from date sheet"""
    schedule = get_object_or_404(ExamSchedule, pk=pk)
    exam_id = schedule.exam.id
    if request.method == 'POST':
        schedule.delete()
        messages.success(request, "Paper removed from date sheet.")
    return redirect('examinations:exam_detail', pk=exam_id)


@login_required
@teacher_required
def exam_marks_entry_view(request, schedule_id):
    """Enter and update subject marks for all students in a class with subject navigation."""
    schedule = get_object_or_404(ExamSchedule.objects.select_related('exam', 'class_room', 'subject'), pk=schedule_id)
    students = Student.objects.filter(current_class=schedule.class_room, status='ACTIVE').select_related('current_section')

    # Fetch all scheduled subjects for this class and exam so teacher can easily switch
    class_schedules = ExamSchedule.objects.filter(
        exam=schedule.exam,
        class_room=schedule.class_room
    ).select_related('subject').order_by('exam_date', 'start_time')

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
                recalculate_single_student_exam_result(schedule.exam, st)
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
                    recalculate_single_student_exam_result(schedule.exam, st)
                except Exception:
                    pass

        ActivityLog.log_activity(
            user=request.user,
            action='UPDATE',
            module='Examinations',
            description=f"Updated {saved_count} marks records for {schedule.class_room.name} : {schedule.subject.name} ({schedule.exam.title})"
        )

        messages.success(request, f"Saved marks for {schedule.subject.name} ({saved_count} students updated). Result cards synchronized!")
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
        'class_schedules': class_schedules,
        'student_rows': student_rows,
    }
    return render(request, 'examinations/marks_entry.html', context)


@login_required
@teacher_required
def exam_direct_marks_entry_view(request, exam_id):
    """Direct Marks Entry Page: Opens full list of all subjects for all students with 1 click."""
    exam = get_object_or_404(Exam.objects.select_related('academic_year'), pk=exam_id)
    classes = list(ClassRoom.objects.all().order_by('numeric_level', 'name'))
    
    selected_class_id = request.GET.get('class_room') or request.POST.get('class_room')
    if selected_class_id:
        class_room = get_object_or_404(ClassRoom, pk=selected_class_id)
    else:
        # Pick first class
        class_room = classes[0] if classes else None

    if not class_room:
        messages.warning(request, "No classes found in the system.")
        return redirect('examinations:exam_list')

    # Auto-ensure all subjects for this class are scheduled in this exam so none are missing
    from apps.academics.models import ClassSubject, Subject
    class_subjects = list(ClassSubject.objects.filter(class_room=class_room).select_related('subject'))
    subjects_to_schedule = [cs.subject for cs in class_subjects]
    if not subjects_to_schedule:
        subjects_to_schedule = list(Subject.objects.all()[:6])

    default_total = 25 if exam.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.QUIZ_UNIT] else (50 if exam.exam_type == Exam.ExamType.MONTHLY_TEST else 100)
    default_passing = 10 if exam.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.QUIZ_UNIT] else (20 if exam.exam_type == Exam.ExamType.MONTHLY_TEST else 33)

    from datetime import time
    exam_date = exam.start_date or timezone.now().date()
    for subj in subjects_to_schedule:
        ExamSchedule.objects.get_or_create(
            exam=exam,
            class_room=class_room,
            subject=subj,
            defaults={
                'exam_date': exam_date,
                'start_time': time(9, 0),
                'end_time': time(11, 0),
                'total_marks': default_total,
                'passing_marks': default_passing,
            }
        )

    schedules = list(exam.schedules.filter(class_room=class_room).select_related('subject').order_by('subject__name'))
    students = list(Student.objects.filter(current_class=class_room, status='ACTIVE').select_related('current_section'))

    # Selected Student (for focused vertical list)
    selected_student_id = request.GET.get('student_id') or request.POST.get('student_id')
    if selected_student_id:
        selected_student = next((s for s in students if str(s.id) == str(selected_student_id)), None)
    else:
        selected_student = students[0] if students else None

    # Handle POST
    if request.method == 'POST':
        # 1. Update Subject Max / Passing Marks if customized by teacher
        for sch in schedules:
            tot_str = request.POST.get(f'total_marks_{sch.id}', '').strip()
            pass_str = request.POST.get(f'pass_marks_{sch.id}', '').strip()
            if tot_str:
                try:
                    tot_val = max(1, int(tot_str))
                    pass_val = int(pass_str) if pass_str else max(1, int(tot_val * 0.4))
                    if sch.total_marks != tot_val or sch.passing_marks != pass_val:
                        sch.total_marks = tot_val
                        sch.passing_marks = pass_val
                        sch.save(update_fields=['total_marks', 'passing_marks'])
                except Exception:
                    pass

        # 2. Update Student Marks
        target_students = [selected_student] if (selected_student and 'save_single_student' in request.POST) else students
        saved_count = 0
        for st in target_students:
            for sch in schedules:
                marks_val_str = request.POST.get(f'marks_{st.id}_{sch.id}', '').strip()
                is_absent = request.POST.get(f'absent_{st.id}_{sch.id}') == '1'
                remarks = request.POST.get(f'remarks_{st.id}_{sch.id}', '').strip()

                if is_absent:
                    ExamMarks.objects.update_or_create(
                        exam_schedule=sch,
                        student=st,
                        defaults={
                            'marks_obtained': Decimal('0.00'),
                            'is_absent': True,
                            'remarks': remarks or 'Absent',
                            'recorded_by': request.user
                        }
                    )
                    saved_count += 1
                elif marks_val_str != '':
                    try:
                        marks_val = Decimal(marks_val_str)
                        marks_val = max(Decimal('0.00'), min(marks_val, Decimal(str(sch.total_marks))))
                        ExamMarks.objects.update_or_create(
                            exam_schedule=sch,
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

            recalculate_single_student_exam_result(exam, st)

        ActivityLog.log_activity(
            user=request.user,
            action='UPDATE',
            module='Examinations',
            description=f"Updated subject marks & custom total marks for {class_room.name} in {exam.title}"
        )

        if selected_student:
            messages.success(request, f"Result card for {selected_student.get_full_name()} generated successfully!")
            return redirect('examinations:student_report_card', exam_id=exam.id, student_id=selected_student.id)
        else:
            messages.success(request, f"Marks and result cards for {class_room.name} saved successfully!")
            return redirect('examinations:class_result', exam_id=exam.id, class_id=class_room.id)

    # Build matrix & vertical subject rows for selected student
    all_marks = ExamMarks.objects.filter(exam_schedule__in=schedules)
    marks_map = {(m.student_id, m.exam_schedule_id): m for m in all_marks}

    class_total_max = sum(sch.total_marks for sch in schedules)

    # Vertical rows for currently selected student
    selected_student_rows = []
    selected_student_obtained = Decimal('0.00')
    if selected_student:
        for sch in schedules:
            m_rec = marks_map.get((selected_student.id, sch.id))
            obt = m_rec.marks_obtained if m_rec and not m_rec.is_absent else None
            is_abs = m_rec.is_absent if m_rec else False
            rem = m_rec.remarks if m_rec else ''
            if obt is not None:
                selected_student_obtained += obt
            
            num_obt = obt if obt is not None else Decimal('0.00')
            pct = (num_obt / Decimal(str(sch.total_marks)) * Decimal('100.00')) if sch.total_marks > 0 else Decimal('0.00')
            sub_grade, _ = GradeScale.get_grade_for_percentage(pct)

            selected_student_rows.append({
                'schedule': sch,
                'subject': sch.subject,
                'total_marks': sch.total_marks,
                'passing_marks': sch.passing_marks,
                'obtained': obt if obt is not None else '',
                'is_absent': is_abs,
                'remarks': rem,
                'percentage': round(pct, 1),
                'grade': sub_grade,
            })

    selected_student_pct = (selected_student_obtained / Decimal(str(class_total_max)) * Decimal('100.00')) if class_total_max > 0 else Decimal('0.00')
    selected_student_grade, _ = GradeScale.get_grade_for_percentage(selected_student_pct)

    context = {
        'page_title': f"Marks Entry - {exam.title}",
        'exam': exam,
        'classes': classes,
        'class_room': class_room,
        'students': students,
        'selected_student': selected_student,
        'schedules': schedules,
        'class_total_max': class_total_max,
        'selected_student_rows': selected_student_rows,
        'selected_student_obtained': selected_student_obtained,
        'selected_student_pct': round(selected_student_pct, 1),
        'selected_student_grade': selected_student_grade,
    }
    return render(request, 'examinations/quick_marks_entry.html', context)


@login_required
@teacher_required
def exam_class_master_marksheet_view(request, exam_id, class_id):
    """Multi-Subject Master Marksheet Grid: Enter/Edit all subjects for all students in one table."""
    exam = get_object_or_404(Exam.objects.select_related('academic_year'), pk=exam_id)
    class_room = get_object_or_404(ClassRoom, pk=class_id)
    schedules = list(exam.schedules.filter(class_room=class_room).select_related('subject').order_by('subject__name'))
    students = list(Student.objects.filter(current_class=class_room, status='ACTIVE').select_related('current_section'))

    if request.method == 'POST':
        saved_count = 0
        for st in students:
            for sch in schedules:
                marks_val_str = request.POST.get(f'marks_{st.id}_{sch.id}', '').strip()
                is_absent = request.POST.get(f'absent_{st.id}_{sch.id}') == '1'
                remarks = request.POST.get(f'remarks_{st.id}_{sch.id}', '').strip()

                if is_absent:
                    ExamMarks.objects.update_or_create(
                        exam_schedule=sch,
                        student=st,
                        defaults={
                            'marks_obtained': Decimal('0.00'),
                            'is_absent': True,
                            'remarks': remarks or 'Absent',
                            'recorded_by': request.user
                        }
                    )
                    saved_count += 1
                elif marks_val_str != '':
                    try:
                        marks_val = Decimal(marks_val_str)
                        marks_val = max(Decimal('0.00'), min(marks_val, Decimal(str(sch.total_marks))))
                        ExamMarks.objects.update_or_create(
                            exam_schedule=sch,
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
            
            # Recalculate result for each student
            recalculate_single_student_exam_result(exam, st)

        ActivityLog.log_activity(
            user=request.user,
            action='UPDATE',
            module='Examinations',
            description=f"Updated Master Marksheet for {class_room.name} ({exam.title})"
        )

        messages.success(request, f"Master marksheet saved successfully! All subject marks and result cards updated.")
        return redirect('examinations:class_master_marksheet', exam_id=exam.id, class_id=class_room.id)

    # Fetch all marks records
    all_marks = ExamMarks.objects.filter(exam_schedule__in=schedules)
    marks_map = {(m.student_id, m.exam_schedule_id): m for m in all_marks}

    student_matrix = []
    class_total_max = sum(sch.total_marks for sch in schedules)

    for st in students:
        sub_entries = []
        st_total_obtained = Decimal('0.00')
        for sch in schedules:
            m_rec = marks_map.get((st.id, sch.id))
            obt = m_rec.marks_obtained if m_rec and not m_rec.is_absent else None
            is_abs = m_rec.is_absent if m_rec else False
            if obt is not None:
                st_total_obtained += obt
            sub_entries.append({
                'schedule': sch,
                'obtained': obt if obt is not None else '',
                'is_absent': is_abs,
                'remarks': m_rec.remarks if m_rec else '',
            })

        pct = (st_total_obtained / Decimal(str(class_total_max)) * Decimal('100.00')) if class_total_max > 0 else Decimal('0.00')
        grade, _ = GradeScale.get_grade_for_percentage(pct)

        student_matrix.append({
            'student': st,
            'subjects': sub_entries,
            'total_obtained': st_total_obtained,
            'percentage': round(pct, 1),
            'grade': grade,
        })

    context = {
        'page_title': f"Master Marksheet - {class_room.name} ({exam.title})",
        'exam': exam,
        'class_room': class_room,
        'schedules': schedules,
        'class_total_max': class_total_max,
        'student_matrix': student_matrix,
    }
    return render(request, 'examinations/class_master_marksheet.html', context)


@login_required
@teacher_required
def auto_schedule_class_subjects_view(request, exam_id, class_id):
    """Auto-populate all curriculum subjects for a class into the exam schedule."""
    exam = get_object_or_404(Exam, pk=exam_id)
    class_room = get_object_or_404(ClassRoom, pk=class_id)
    
    # Determine default total marks based on exam type
    default_total = 100
    default_passing = 33
    if exam.exam_type in [Exam.ExamType.WEEKLY_TEST, Exam.ExamType.QUIZ_UNIT]:
        default_total = 25
        default_passing = 10
    elif exam.exam_type == Exam.ExamType.MONTHLY_TEST:
        default_total = 50
        default_passing = 20

    # Get class subjects or default subjects
    from apps.academics.models import ClassSubject, Subject
    class_subjects = list(ClassSubject.objects.filter(class_room=class_room).select_related('subject'))
    subjects_to_add = [cs.subject for cs in class_subjects]
    if not subjects_to_add:
        subjects_to_add = list(Subject.objects.all()[:6])

    added_count = 0
    exam_date = exam.start_date or timezone.now().date()
    from datetime import time

    for idx, subj in enumerate(subjects_to_add):
        sch, created = ExamSchedule.objects.get_or_create(
            exam=exam,
            class_room=class_room,
            subject=subj,
            defaults={
                'exam_date': exam_date,
                'start_time': time(9, 0),
                'end_time': time(11, 0),
                'total_marks': default_total,
                'passing_marks': default_passing,
            }
        )
        if created:
            added_count += 1

    messages.success(request, f"Added {added_count} subjects to date sheet for {class_room.name}.")
    return redirect('examinations:exam_detail', pk=exam.pk)


@login_required
@teacher_required
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
@teacher_required
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


def recalculate_single_student_exam_result(exam, student):
    """Compute and update ExamStudentResult and ranks for a single student."""
    class_room = student.current_class
    if not class_room:
        return None

    schedules = list(exam.schedules.filter(class_room=class_room))
    if not schedules:
        return None

    class_total_max_marks = sum(s.total_marks for s in schedules)
    marks_list = list(ExamMarks.objects.filter(exam_schedule__in=schedules, student=student))
    
    # Sum of marks obtained
    obtained_sum = sum(m.marks_obtained for m in marks_list if not m.is_absent)
    
    # Check if failed or absent in any paper
    has_failed_paper = False
    for sch in schedules:
        m = next((item for item in marks_list if item.exam_schedule_id == sch.id), None)
        if not m or m.is_absent or m.marks_obtained < sch.passing_marks:
            has_failed_paper = True

    pct = (obtained_sum / Decimal(str(class_total_max_marks)) * Decimal('100.00')) if class_total_max_marks > 0 else Decimal('0.00')
    grade, remarks = GradeScale.get_grade_for_percentage(pct)
    is_passed = (not has_failed_paper) and (pct >= Decimal('33.00'))

    res_obj, _ = ExamStudentResult.objects.update_or_create(
        exam=exam,
        student=student,
        defaults={
            'class_room': class_room,
            'section': student.current_section,
            'total_marks': Decimal(str(class_total_max_marks)),
            'obtained_marks': obtained_sum,
            'percentage': round(pct, 2),
            'grade': grade,
            'grade_remarks': remarks,
            'is_passed': is_passed,
        }
    )

    # Re-calculate ranks for the class
    all_class_results = list(ExamStudentResult.objects.filter(exam=exam, class_room=class_room).order_by('-percentage'))
    for rank, res in enumerate(all_class_results, start=1):
        if res.position_in_class != rank:
            res.position_in_class = rank
            res.save(update_fields=['position_in_class'])

    # Re-calculate section ranks
    if student.current_section:
        sec_results = list(ExamStudentResult.objects.filter(exam=exam, class_room=class_room, section=student.current_section).order_by('-percentage'))
        for s_rank, s_res in enumerate(sec_results, start=1):
            if s_res.position_in_section != s_rank:
                s_res.position_in_section = s_rank
                s_res.save(update_fields=['position_in_section'])

    return res_obj


@login_required
@teacher_required
def student_marks_edit_view(request, exam_id, student_id):
    """Edit all subject marks for a specific student in one simple, clean page."""
    exam = get_object_or_404(Exam.objects.select_related('academic_year'), pk=exam_id)
    student = get_object_or_404(
        Student.objects.select_related('current_class', 'current_section'),
        pk=student_id
    )
    
    schedules = exam.schedules.filter(class_room=student.current_class).select_related('subject').order_by('exam_date', 'start_time')
    existing_marks = {m.exam_schedule_id: m for m in ExamMarks.objects.filter(exam_schedule__in=schedules, student=student)}
    
    if request.method == 'POST':
        saved_count = 0
        for sch in schedules:
            marks_str = request.POST.get(f'marks_{sch.id}', '').strip()
            is_absent = request.POST.get(f'absent_{sch.id}') == '1'
            remarks = request.POST.get(f'remarks_{sch.id}', '').strip()

            if is_absent:
                ExamMarks.objects.update_or_create(
                    exam_schedule=sch,
                    student=student,
                    defaults={
                        'marks_obtained': Decimal('0.00'),
                        'is_absent': True,
                        'remarks': remarks or 'Absent',
                        'recorded_by': request.user
                    }
                )
                saved_count += 1
            elif marks_str != '':
                try:
                    marks_val = Decimal(marks_str)
                    marks_val = max(Decimal('0.00'), min(marks_val, Decimal(str(sch.total_marks))))
                    ExamMarks.objects.update_or_create(
                        exam_schedule=sch,
                        student=student,
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

        # Recalculate result card
        recalculate_single_student_exam_result(exam, student)

        ActivityLog.log_activity(
            user=request.user,
            action='UPDATE',
            module='Examinations',
            description=f"Updated subject marks for {student.get_full_name()} in {exam.title}"
        )

        messages.success(request, f"Marks and result card for {student.get_full_name()} updated successfully.")
        
        if 'save_and_view' in request.POST:
            return redirect('examinations:student_report_card', exam_id=exam.id, student_id=student.id)
        return redirect('examinations:student_marks_edit', exam_id=exam.id, student_id=student.id)

    # Prepare subject rows for display
    subject_rows = []
    total_max = 0
    total_obtained = Decimal('0.00')
    for sch in schedules:
        mark_rec = existing_marks.get(sch.id)
        obt = mark_rec.marks_obtained if mark_rec and not mark_rec.is_absent else None
        is_abs = mark_rec.is_absent if mark_rec else False
        rem = mark_rec.remarks if mark_rec else ''
        total_max += sch.total_marks
        if obt is not None:
            total_obtained += obt

        subject_rows.append({
            'schedule': sch,
            'subject': sch.subject,
            'total_marks': sch.total_marks,
            'passing_marks': sch.passing_marks,
            'obtained': obt if obt is not None else '',
            'is_absent': is_abs,
            'remarks': rem,
        })

    result = ExamStudentResult.objects.filter(exam=exam, student=student).first()

    context = {
        'page_title': f"Edit Student Marks - {student.get_full_name()} ({exam.title})",
        'exam': exam,
        'student': student,
        'schedules': schedules,
        'subject_rows': subject_rows,
        'total_max': total_max,
        'total_obtained': total_obtained,
        'result': result,
    }
    return render(request, 'examinations/student_marks_edit.html', context)


@login_required
def student_report_card_view(request, exam_id, student_id):
    """Printable & editable official report card for a student."""
    exam = Exam.objects.filter(pk=exam_id).first()
    if not exam:
        # Fallback to latest published exam if an outdated ID was cached
        exam = Exam.objects.filter(is_published=True).order_by('id').first()
        if not exam:
            messages.error(request, "Examination record not found.")
            return redirect('examinations:exam_list')

    student = Student.objects.filter(pk=student_id).select_related('current_class', 'current_section', 'academic_year').first()
    if not student:
        if getattr(request.user, 'is_student', False) and hasattr(request.user, 'student_profile'):
            student = request.user.student_profile
        else:
            student = Student.objects.first()
        if not student:
            messages.error(request, "Student record not found.")
            return redirect('examinations:exam_list')
    
    if getattr(request.user, 'is_student', False):
        if hasattr(request.user, 'student_profile') and student != request.user.student_profile:
            messages.error(request, "Unauthorized access to report card.")
            return redirect('students:student_dashboard')

    schedules = list(exam.schedules.filter(class_room=student.current_class).select_related('subject').order_by('exam_date', 'start_time'))

    # If teacher submits subject marks from the Result Card itself
    if request.method == 'POST' and not getattr(request.user, 'is_student', False):
        saved_count = 0
        for sch in schedules:
            marks_str = request.POST.get(f'marks_{sch.id}', '').strip()
            is_absent = request.POST.get(f'absent_{sch.id}') == '1'
            remarks = request.POST.get(f'remarks_{sch.id}', '').strip()

            if is_absent:
                ExamMarks.objects.update_or_create(
                    exam_schedule=sch,
                    student=student,
                    defaults={
                        'marks_obtained': Decimal('0.00'),
                        'is_absent': True,
                        'remarks': remarks or 'Absent',
                        'recorded_by': request.user
                    }
                )
                saved_count += 1
            elif marks_str != '':
                try:
                    marks_val = Decimal(marks_str)
                    marks_val = max(Decimal('0.00'), min(marks_val, Decimal(str(sch.total_marks))))
                    ExamMarks.objects.update_or_create(
                        exam_schedule=sch,
                        student=student,
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

        # Recalculate result
        recalculate_single_student_exam_result(exam, student)

        ActivityLog.log_activity(
            user=request.user,
            action='UPDATE',
            module='Examinations',
            description=f"Updated subject marks and result card for {student.get_full_name()} ({exam.title})"
        )

        messages.success(request, f"Result card for {student.get_full_name()} saved successfully! All subject marks and grand totals updated.")
        return redirect('examinations:student_report_card', exam_id=exam.id, student_id=student.id)

    result = ExamStudentResult.objects.filter(exam=exam, student=student).first()

    marks_rows = []
    for sch in schedules:
        m_rec = ExamMarks.objects.filter(exam_schedule=sch, student=student).first()
        obt = m_rec.marks_obtained if m_rec and not m_rec.is_absent else None
        is_abs = m_rec.is_absent if m_rec else False
        num_obt = obt if obt is not None else Decimal('0.00')
        pct = (num_obt / Decimal(str(sch.total_marks)) * Decimal('100.00')) if sch.total_marks > 0 else Decimal('0.00')
        sub_grade, sub_rem = GradeScale.get_grade_for_percentage(pct)

        marks_rows.append({
            'schedule': sch,
            'subject': sch.subject,
            'total_marks': sch.total_marks,
            'passing_marks': sch.passing_marks,
            'obtained': obt if obt is not None else '',
            'num_obtained': num_obt,
            'is_absent': is_abs,
            'percentage': round(pct, 1),
            'grade': sub_grade,
            'remarks': m_rec.remarks if m_rec else '',
            'is_pass': (num_obt >= sch.passing_marks) and not is_abs,
        })

    # Attendance stats for this student
    attendance_count = student.attendance_records.count()
    presents_count = student.attendance_records.filter(status='PRESENT').count()
    attendance_rate = round((presents_count / attendance_count * 100), 1) if attendance_count > 0 else 100.0
    is_staff = not getattr(request.user, 'is_student', False)

    context = {
        'page_title': f"Report Card - {student.get_full_name()} ({exam.title})",
        'exam': exam,
        'student': student,
        'result': result,
        'marks_rows': marks_rows,
        'attendance_count': attendance_count,
        'attendance_rate': attendance_rate,
        'is_staff': is_staff,
    }
    return render(request, 'examinations/report_card.html', context)


@login_required
@principal_required
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


from .models import OnlineAssessment, AssessmentQuestion, StudentAssessmentAttempt


@login_required
def cbt_assessment_list_view(request):
    """List of all online CBT quizzes and tests."""
    quizzes = OnlineAssessment.objects.select_related('class_room', 'subject', 'created_by').annotate(
        questions_count=Count('questions', distinct=True),
        attempts_count=Count('attempts', distinct=True)
    )

    if not quizzes.exists():
        classroom = ClassRoom.objects.first()
        subject = Subject.objects.first()
        if classroom and subject:
            q = OnlineAssessment.objects.create(
                title="Physics Mid-Term CBT MCQ Assessment",
                class_room=classroom,
                subject=subject,
                duration_minutes=20,
                total_marks=Decimal('10.00'),
                passing_percentage=Decimal('50.00'),
                status=OnlineAssessment.Status.PUBLISHED,
                created_by=request.user
            )
            AssessmentQuestion.objects.create(
                assessment=q,
                question_text="What is the standard SI unit of acceleration?",
                question_type=AssessmentQuestion.QuestionType.MCQ,
                option_a="m/s",
                option_b="m/s²",
                option_c="km/h",
                option_d="Newton",
                correct_answer="B",
                marks=Decimal('2.00'),
                order_num=1
            )
            AssessmentQuestion.objects.create(
                assessment=q,
                question_text="Acceleration due to gravity on Earth is approximately 9.8 m/s².",
                question_type=AssessmentQuestion.QuestionType.TRUE_FALSE,
                option_a="True",
                option_b="False",
                correct_answer="TRUE",
                marks=Decimal('2.00'),
                order_num=2
            )
            AssessmentQuestion.objects.create(
                assessment=q,
                question_text="Which of the following is a scalar quantity?",
                question_type=AssessmentQuestion.QuestionType.MCQ,
                option_a="Velocity",
                option_b="Force",
                option_c="Mass",
                option_d="Displacement",
                correct_answer="C",
                marks=Decimal('2.00'),
                order_num=3
            )
            AssessmentQuestion.objects.create(
                assessment=q,
                question_text="Newton's First Law is also known as the Law of Inertia.",
                question_type=AssessmentQuestion.QuestionType.TRUE_FALSE,
                option_a="True",
                option_b="False",
                correct_answer="TRUE",
                marks=Decimal('2.00'),
                order_num=4
            )
            AssessmentQuestion.objects.create(
                assessment=q,
                question_text="Rate of change of displacement is known as:",
                question_type=AssessmentQuestion.QuestionType.MCQ,
                option_a="Speed",
                option_b="Velocity",
                option_c="Work",
                option_d="Power",
                correct_answer="B",
                marks=Decimal('2.00'),
                order_num=5
            )
            quizzes = OnlineAssessment.objects.select_related('class_room', 'subject', 'created_by').annotate(
                questions_count=Count('questions', distinct=True),
                attempts_count=Count('attempts', distinct=True)
            )

    return render(request, 'examinations/cbt_quiz_list.html', {
        'quizzes': quizzes,
        'page_title': 'Online CBT Examinations & Assessments'
    })


@login_required
def cbt_assessment_create_view(request):
    """Create a new timed CBT quiz."""
    classes = ClassRoom.objects.all()
    subjects = Subject.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        class_id = request.POST.get('class_room')
        subject_id = request.POST.get('subject')
        duration = int(request.POST.get('duration_minutes', 30))
        pass_pct = Decimal(request.POST.get('passing_percentage', '40.00'))

        quiz = OnlineAssessment.objects.create(
            title=title,
            class_room_id=class_id,
            subject_id=subject_id,
            duration_minutes=duration,
            passing_percentage=pass_pct,
            created_by=request.user,
            status=OnlineAssessment.Status.PUBLISHED
        )
        messages.success(request, f"Online Assessment '{title}' created! Now add questions.")
        return redirect('examinations:cbt_questions', pk=quiz.id)

    return render(request, 'examinations/cbt_quiz_form.html', {
        'classes': classes,
        'subjects': subjects,
        'page_title': 'Create Online CBT Assessment'
    })


@login_required
def cbt_assessment_questions_view(request, pk):
    """Add and manage questions for online assessment."""
    quiz = get_object_or_404(OnlineAssessment.objects.select_related('class_room', 'subject'), pk=pk)
    questions = quiz.questions.all()

    if request.method == 'POST' and 'add_question' in request.POST:
        q_text = request.POST.get('question_text')
        q_type = request.POST.get('question_type', AssessmentQuestion.QuestionType.MCQ)
        opt_a = request.POST.get('option_a', '')
        opt_b = request.POST.get('option_b', '')
        opt_c = request.POST.get('option_c', '')
        opt_d = request.POST.get('option_d', '')
        ans = request.POST.get('correct_answer', 'A')
        marks = Decimal(request.POST.get('marks', '2.00'))
        order_num = questions.count() + 1

        AssessmentQuestion.objects.create(
            assessment=quiz,
            question_text=q_text,
            question_type=q_type,
            option_a=opt_a,
            option_b=opt_b,
            option_c=opt_c,
            option_d=opt_d,
            correct_answer=ans.upper(),
            marks=marks,
            order_num=order_num
        )
        # Recalculate total marks
        quiz.total_marks = sum(q.marks for q in quiz.questions.all())
        quiz.save()

        messages.success(request, "Question added to quiz!")
        return redirect('examinations:cbt_questions', pk=quiz.id)

    return render(request, 'examinations/cbt_quiz_questions.html', {
        'quiz': quiz,
        'questions': questions,
        'page_title': f"Questions: {quiz.title}"
    })


@login_required
def cbt_assessment_take_view(request, pk):
    """Interactive student test-taking interface with auto-grading."""
    quiz = get_object_or_404(OnlineAssessment.objects.select_related('class_room', 'subject'), pk=pk)
    questions = list(quiz.questions.all())
    
    # Get active student
    student = Student.objects.filter(status='ACTIVE').first()
    if request.user.role == 'STUDENT':
        student = getattr(request.user, 'student_profile', student)

    attempt = StudentAssessmentAttempt.objects.filter(assessment=quiz, student=student).first()

    if request.method == 'POST' and not attempt:
        # Evaluate answers
        total_score = Decimal('0.00')
        answers = {}
        for q in questions:
            user_choice = request.POST.get(f'question_{q.id}', '').strip().upper()
            answers[str(q.id)] = user_choice
            if user_choice and user_choice == q.correct_answer.strip().upper():
                total_score += q.marks

        pct = (total_score / quiz.total_marks * Decimal('100.00')) if quiz.total_marks > 0 else Decimal('0.00')
        is_pass = (pct >= quiz.passing_percentage)

        attempt = StudentAssessmentAttempt.objects.create(
            assessment=quiz,
            student=student,
            submitted_at=timezone.now(),
            score_obtained=total_score,
            percentage=round(pct, 2),
            is_passed=is_pass,
            answers_payload=answers
        )

        messages.success(request, f"Test submitted successfully! You scored {total_score}/{quiz.total_marks} ({round(pct,1)}%).")

    return render(request, 'examinations/cbt_quiz_take.html', {
        'quiz': quiz,
        'questions': questions,
        'student': student,
        'attempt': attempt,
        'page_title': f"CBT Assessment: {quiz.title}"
    })


@login_required
def cbt_assessment_results_view(request, pk):
    """View cohort performance & score ranking for CBT assessment."""
    quiz = get_object_or_404(OnlineAssessment.objects.select_related('class_room', 'subject'), pk=pk)
    attempts = quiz.attempts.select_related('student').order_by('-score_obtained')
    
    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0.0
    passed_count = attempts.filter(is_passed=True).count()
    pass_rate = round((passed_count / attempts.count() * 100), 1) if attempts.exists() else 0.0

    return render(request, 'examinations/cbt_quiz_results.html', {
        'quiz': quiz,
        'attempts': attempts,
        'avg_score': round(avg_score, 1),
        'pass_rate': pass_rate,
        'page_title': f"Results: {quiz.title}"
    })

