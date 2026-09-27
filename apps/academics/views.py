from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from apps.accounts.decorators import coordinator_required
from apps.core.models import ActivityLog
from .models import AcademicYear, ClassRoom, Section, Subject, ClassSubject
from .forms import AcademicYearForm, ClassRoomForm, SectionForm, SubjectForm, ClassSubjectForm


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
                messages.success(request, f"Class {c.name} added successfully!")
                return redirect('academics:class_list')
            else:
                messages.error(request, "Failed to create class. Check errors below.")

        elif action == 'add_section':
            section_form = SectionForm(request.POST)
            if section_form.is_valid():
                s = section_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Added Section {s}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Section {s} added successfully!")
                return redirect('academics:class_list')
            else:
                messages.error(request, "Failed to create section. Check errors below.")

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
            messages.error(request, f"Cannot delete {class_obj.name} because students are currently enrolled.")
        else:
            name = class_obj.name
            class_obj.delete()
            ActivityLog.log_activity(request.user, 'DELETE', 'Academics', f"Deleted Class {name}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Class {name} deleted successfully.")
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
        elif action == 'assign_subject':
            assign_form = ClassSubjectForm(request.POST)
            if assign_form.is_valid():
                cs = assign_form.save()
                ActivityLog.log_activity(request.user, 'CREATE', 'Academics', f"Assigned {cs}", request.META.get('REMOTE_ADDR'))
                messages.success(request, f"Subject assigned to {cs.class_room.name} successfully!")
                return redirect('academics:subject_list')

    return render(request, 'academics/subject_list.html', {
        'subjects': subjects,
        'assignments': assignments,
        'subject_form': subject_form,
        'assign_form': assign_form,
        'page_title': 'Subjects & Curriculum'
    })


@login_required
def api_get_sections(request, class_id):
    """API endpoint to get sections for a specific class for dynamic AJAX dropdowns"""
    sections = Section.objects.filter(class_room_id=class_id).values('id', 'name', 'capacity')
    return JsonResponse({'sections': list(sections)})
