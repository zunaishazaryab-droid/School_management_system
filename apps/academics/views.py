from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.accounts.decorators import coordinator_required
from apps.core.models import ActivityLog
from .models import AcademicYear, ClassRoom, Section, Subject, ClassSubject, Period, TimetableEntry
from .forms import AcademicYearForm, ClassRoomForm, SectionForm, SubjectForm, ClassSubjectForm, PeriodForm, TimetableEntryForm


@login_required
@coordinator_required
def class_list_view(request):
    classes = ClassRoom.objects.prefetch_related('sections', 'sections__students', 'students').all()
    sections = Section.objects.select_related('class_room', 'class_teacher').all()
    academic_years = AcademicYear.objects.all()

    class_form = ClassRoomForm()
    section_form = SectionForm()
    year_form = AcademicYearForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_class':
            class_form = ClassRoomForm(request.POST)
            if class_form.is_valid():
                c = class_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Added Class {c.name}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Class '{c.name}' added successfully!")
                return redirect('academics:class_list')
            else:
                messages.error(request, "Failed to create class. Please check the entered data.")

        elif action == 'edit_class':
            class_id = request.POST.get('class_id')
            class_obj = get_object_or_404(ClassRoom, pk=class_id)
            edit_form = ClassRoomForm(request.POST, instance=class_obj)
            if edit_form.is_valid():
                c = edit_form.save()
                ActivityLog.log_activity(request.user, 'UPDATE', 'Academics', f"Updated Class {c.name}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Class '{c.name}' updated successfully!")
                return redirect('academics:class_list')
            else:
                messages.error(request, "Failed to update class. Please check the entered data.")

        elif action == 'add_section':
            section_form = SectionForm(request.POST)
            if section_form.is_valid():
                s = section_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Added Section {s}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Section '{s.name}' added to {s.class_room.name} successfully!")
                return redirect('academics:class_list')
            else:
                messages.error(request, "Failed to create section. Please check the entered data.")

        elif action == 'edit_section':
            section_id = request.POST.get('section_id')
            section_obj = get_object_or_404(Section, pk=section_id)
            edit_sec_form = SectionForm(request.POST, instance=section_obj)
            if edit_sec_form.is_valid():
                s = edit_sec_form.save()
                ActivityLog.log_activity(request.user, 'UPDATE', 'Academics', f"Updated Section {s}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Section '{s.name}' updated successfully!")
                return redirect('academics:class_list')
            else:
                messages.error(request, "Failed to update section. Please check the entered data.")

        elif action == 'add_year':
            year_form = AcademicYearForm(request.POST)
            if year_form.is_valid():
                y = year_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Added Academic Year {y.name}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Academic Year {y.name} added successfully!")
                return redirect('academics:class_list')

    return render(request, 'academics/class_list.html', {
        'classes': classes,
        'sections': sections,
        'academic_years': academic_years,
        'class_form': class_form,
        'section_form': section_form,
        'year_form': year_form,
        'page_title': 'Classes & Sections'
    })


@login_required
@coordinator_required
def class_delete_view(request, pk):
    class_obj = get_object_or_404(ClassRoom, pk=pk)
    if request.method == 'POST':
        if class_obj.students.exists():
            messages.error(request, f"Cannot delete '{class_obj.name}' because students are currently enrolled in it.")
        elif class_obj.sections.filter(students__isnull=False).exists():
            messages.error(request, f"Cannot delete '{class_obj.name}' because one of its sections has enrolled students.")
        else:
            name = class_obj.name
            class_obj.delete()
            ActivityLog.log_activity(request.user, 'DELETE', 'Academics', f"Deleted Class {name}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Class '{name}' deleted successfully.")
    return redirect('academics:class_list')


@login_required
@coordinator_required
def section_delete_view(request, pk):
    section_obj = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        if section_obj.students.exists():
            messages.error(request, f"Cannot delete Section '{section_obj.name}' because students are currently enrolled in it.")
        else:
            sec_name = f"{section_obj.class_room.name} - Section {section_obj.name}"
            section_obj.delete()
            ActivityLog.log_activity(request.user, 'DELETE', 'Academics', f"Deleted Section {sec_name}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Section '{sec_name}' deleted successfully.")
    return redirect('academics:class_list')


@login_required
@coordinator_required
def subject_list_view(request):
    subjects = Subject.objects.all()
    assignments = ClassSubject.objects.select_related('class_room', 'section', 'subject', 'teacher').all()
    
    subject_form = SubjectForm()
    assign_form = ClassSubjectForm()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_subject':
            subject_form = SubjectForm(request.POST)
            if subject_form.is_valid():
                s = subject_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Created Subject {s.name}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Subject {s.name} created successfully!")
                return redirect('academics:subject_list')
        elif action == 'edit_subject':
            subject_id = request.POST.get('subject_id')
            subject_obj = get_object_or_404(Subject, pk=subject_id)
            edit_form = SubjectForm(request.POST, instance=subject_obj)
            if edit_form.is_valid():
                s = edit_form.save()
                ActivityLog.log_activity(request.user, 'UPDATE', 'Academics', f"Updated Subject {s.name}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Subject '{s.name}' updated successfully!")
                return redirect('academics:subject_list')
            else:
                messages.error(request, "Failed to update subject. Check entered details.")

        elif action == 'assign_subject':
            assign_form = ClassSubjectForm(request.POST)
            if assign_form.is_valid():
                cs = assign_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Assigned {cs}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Subject assigned to {cs.class_room.name} successfully!")
                return redirect('academics:subject_list')

        elif action == 'delete_assignment':
            asg_id = request.POST.get('assignment_id')
            asg_obj = get_object_or_404(ClassSubject, pk=asg_id)
            asg_obj.delete()
            messages.success(request, "Subject assignment removed.")
            return redirect('academics:subject_list')

    return render(request, 'academics/subject_list.html', {
        'subjects': subjects,
        'assignments': assignments,
        'subject_form': subject_form,
        'assign_form': assign_form,
        'page_title': 'Subjects & Curriculum'
    })


@login_required
@coordinator_required
def subject_delete_view(request, pk):
    subject_obj = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        name = subject_obj.name
        subject_obj.delete()
        ActivityLog.log_activity(request.user, 'DELETE', 'Academics', f"Deleted Subject {name}", request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Subject '{name}' deleted successfully.")
    return redirect('academics:subject_list')


@login_required
def api_get_sections(request, class_id):
    """API endpoint to get sections for a specific class for dynamic AJAX dropdowns"""
    sections = Section.objects.filter(class_room_id=class_id).values('id', 'name', 'capacity')
    return JsonResponse({'sections': list(sections)})


@login_required
def timetable_view(request):
    """Class-wise and Teacher-wise weekly timetable schedule"""
    from .models import Period, TimetableEntry
    from .forms import PeriodForm, TimetableEntryForm
    from apps.accounts.models import User

    academic_year = AcademicYear.objects.filter(is_current=True).first()
    classes = ClassRoom.objects.all()
    teachers = User.objects.filter(role__in=[User.Role.TEACHER, User.Role.COORDINATOR])
    periods = Period.objects.all().order_by('period_number', 'start_time')

    view_mode = request.GET.get('mode', 'class')  # 'class' or 'teacher'
    selected_class_id = request.GET.get('class_room')
    selected_section_id = request.GET.get('section')
    selected_teacher_id = request.GET.get('teacher')

    selected_class = None
    selected_section = None
    selected_teacher = None

    if selected_class_id:
        selected_class = ClassRoom.objects.filter(id=selected_class_id).first()
        if selected_class and selected_section_id:
            selected_section = selected_class.sections.filter(id=selected_section_id).first()
        elif selected_class:
            selected_section = selected_class.sections.first()
    else:
        selected_class = classes.first()
        if selected_class:
            selected_section = selected_class.sections.first()

    if selected_teacher_id:
        selected_teacher = teachers.filter(id=selected_teacher_id).first()
    elif view_mode == 'teacher':
        selected_teacher = teachers.first()

    days = [
        ('MONDAY', 'Monday'),
        ('TUESDAY', 'Tuesday'),
        ('WEDNESDAY', 'Wednesday'),
        ('THURSDAY', 'Thursday'),
        ('FRIDAY', 'Friday'),
        ('SATURDAY', 'Saturday'),
    ]

    # Handle slot form submission
    slot_form = TimetableEntryForm(initial={
        'academic_year': academic_year,
        'class_room': selected_class,
        'section': selected_section
    })
    period_form = PeriodForm()

    if request.method == 'POST' and 'add_slot' in request.POST:
        slot_form = TimetableEntryForm(request.POST)
        if slot_form.is_valid():
            # Check for conflict: teacher already booked at this day and period
            teacher = slot_form.cleaned_data.get('teacher')
            day = slot_form.cleaned_data['day_of_week']
            period = slot_form.cleaned_data['period']
            cl = slot_form.cleaned_data['class_room']
            sec = slot_form.cleaned_data['section']

            conflict = False
            if teacher:
                conflict = TimetableEntry.objects.filter(
                    academic_year=academic_year,
                    day_of_week=day,
                    period=period,
                    teacher=teacher
                ).exclude(class_room=cl, section=sec).first()

            if conflict:
                messages.error(request, f"Schedule Conflict! Teacher {teacher.get_full_name()} is already assigned to {conflict.class_room.name} ({conflict.section.name}) for {period.name} on {day}.")
            else:
                entry, created = TimetableEntry.objects.update_or_create(
                    academic_year=academic_year,
                    class_room=cl,
                    section=sec,
                    day_of_week=day,
                    period=period,
                    defaults={
                        'subject': slot_form.cleaned_data['subject'],
                        'teacher': teacher,
                        'room_number': slot_form.cleaned_data.get('room_number', ''),
                    }
                )
                messages.success(request, f"Timetable slot saved for {entry.class_room.name} ({entry.section.name}) on {day} {period.name}.")
                return redirect(f"{request.path}?mode=class&class_room={cl.id}&section={sec.id}")
        else:
            messages.error(request, "Failed to save slot. Please check form inputs.")

    elif request.method == 'POST' and 'add_period' in request.POST:
        period_form = PeriodForm(request.POST)
        if period_form.is_valid():
            p = period_form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Created Period {p.name}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Period '{p.name}' created.")
            return redirect(request.get_full_path())
        else:
            messages.error(request, "Failed to create period. Check entered details.")

    elif request.method == 'POST' and 'edit_period' in request.POST:
        period_id = request.POST.get('period_id')
        p_obj = get_object_or_404(Period, pk=period_id)
        period_form = PeriodForm(request.POST, instance=p_obj)
        if period_form.is_valid():
            p = period_form.save()
            ActivityLog.log_activity(request.user, 'UPDATE', 'Academics', f"Updated Period {p.name}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Period '{p.name}' updated successfully.")
            return redirect(request.get_full_path())
        else:
            messages.error(request, "Failed to update period. Check entered details.")

    elif request.method == 'POST' and 'delete_period' in request.POST:
        period_id = request.POST.get('period_id')
        p_obj = get_object_or_404(Period, pk=period_id)
        p_name = p_obj.name
        p_obj.delete()
        ActivityLog.log_activity(request.user, 'DELETE', 'Academics', f"Deleted Period {p_name}", request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Period '{p_name}' deleted.")
        return redirect(request.get_full_path())

    # Build weekly grid matrix [Day][Period] -> Entry
    grid_matrix = []
    for day_code, day_name in days:
        period_cells = []
        for p in periods:
            if p.is_break:
                period_cells.append({'period': p, 'entry': None, 'is_break': True})
            else:
                entry = None
                if view_mode == 'class' and selected_class and selected_section:
                    entry = TimetableEntry.objects.filter(
                        academic_year=academic_year,
                        class_room=selected_class,
                        section=selected_section,
                        day_of_week=day_code,
                        period=p
                    ).select_related('subject', 'teacher').first()
                elif view_mode == 'teacher' and selected_teacher:
                    entry = TimetableEntry.objects.filter(
                        academic_year=academic_year,
                        teacher=selected_teacher,
                        day_of_week=day_code,
                        period=p
                    ).select_related('class_room', 'section', 'subject').first()

                period_cells.append({'period': p, 'entry': entry, 'is_break': False})
        grid_matrix.append({'day_code': day_code, 'day_name': day_name, 'periods': period_cells})

    context = {
        'page_title': 'Class & Teacher Timetable',
        'classes': classes,
        'teachers': teachers,
        'periods': periods,
        'days': days,
        'view_mode': view_mode,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'selected_teacher': selected_teacher,
        'grid_matrix': grid_matrix,
        'slot_form': slot_form,
        'period_form': period_form,
    }
    return render(request, 'academics/timetable.html', context)


@login_required
def timetable_entry_delete_view(request, pk):
    """Delete a timetable entry slot"""
    from .models import TimetableEntry
    entry = get_object_or_404(TimetableEntry, pk=pk)
    cl_id = entry.class_room.id
    sec_id = entry.section.id
    if request.method == 'POST':
        entry.delete()
        messages.success(request, "Timetable slot cleared.")
    return redirect(f"/academics/timetable/?mode=class&class_room={cl_id}&section={sec_id}")


@login_required
@coordinator_required
def period_delete_view(request, pk):
    """Delete a period"""
    from .models import Period
    period_obj = get_object_or_404(Period, pk=pk)
    if request.method == 'POST':
        name = period_obj.name
        period_obj.delete()
        ActivityLog.log_activity(request.user, 'DELETE', 'Academics', f"Deleted Period {name}", request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Period '{name}' deleted successfully.")
    return redirect('academics:timetable')


