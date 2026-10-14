from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from apps.accounts.decorators import teacher_required
from apps.core.models import ActivityLog
from apps.academics.models import ClassRoom, Section, Subject
from apps.students.models import Student
from .models import DailyLecture, Homework, HomeworkSubmission
from .forms import DailyLectureForm, HomeworkForm


@login_required
def lecture_list_view(request):
    """
    Class-wise lectures list.
    Teachers/Admins can record, upload, edit, and delete lectures.
    Students/Parents can view and listen to lectures in read-only mode.
    """
    is_student = getattr(request.user, 'is_student', False) or hasattr(request.user, 'student_profile')
    can_manage_lectures = not is_student and (
        request.user.is_superuser or 
        getattr(request.user, 'is_teacher', False) or 
        getattr(request.user, 'is_principal', False) or 
        getattr(request.user, 'is_admin', False)
    )

    lectures = DailyLecture.objects.select_related('class_room', 'section', 'subject', 'teacher').all()

    student = None
    if is_student and hasattr(request.user, 'student_profile'):
        student = request.user.student_profile
        lectures = lectures.filter(class_room=student.current_class, section=student.current_section)
    else:
        class_id = request.GET.get('class_id')
        if class_id:
            lectures = lectures.filter(class_room_id=class_id)
        
        section_id = request.GET.get('section_id')
        if section_id:
            lectures = lectures.filter(section_id=section_id)

    subject_id = request.GET.get('subject_id')
    if subject_id:
        lectures = lectures.filter(subject_id=subject_id)

    date_filter = request.GET.get('date')
    if date_filter:
        lectures = lectures.filter(date=date_filter)

    search_query = request.GET.get('q', '').strip()
    if search_query:
        lectures = lectures.filter(
            Q(topic__icontains=search_query) |
            Q(chapter_name__icontains=search_query) |
            Q(classwork_description__icontains=search_query) |
            Q(subject__name__icontains=search_query)
        )

    # Class-wise grouping & statistics
    classes = ClassRoom.objects.all().prefetch_related('sections')
    subjects = Subject.objects.all()

    audio_lectures_count = lectures.exclude(audio_recording='').exclude(audio_recording__isnull=True).count()
    total_lectures_count = lectures.count()

    return render(request, 'lectures/lecture_list.html', {
        'lectures': lectures,
        'classes': classes,
        'subjects': subjects,
        'student': student,
        'is_student': is_student,
        'can_manage_lectures': can_manage_lectures,
        'audio_lectures_count': audio_lectures_count,
        'total_lectures_count': total_lectures_count,
        'selected_class_id': request.GET.get('class_id', ''),
        'selected_subject_id': request.GET.get('subject_id', ''),
        'selected_date': date_filter or '',
        'search_query': search_query,
        'page_title': 'Class-Wise Lectures & Audio Recordings'
    })


@login_required
def lecture_detail_view(request, pk):
    """View lecture details, audio player, notes, and homework."""
    lecture = get_object_or_404(
        DailyLecture.objects.select_related('class_room', 'section', 'subject', 'teacher'),
        pk=pk
    )
    is_student = getattr(request.user, 'is_student', False) or hasattr(request.user, 'student_profile')
    can_manage_lectures = not is_student and (
        request.user.is_superuser or 
        getattr(request.user, 'is_teacher', False) or 
        getattr(request.user, 'is_principal', False) or 
        getattr(request.user, 'is_admin', False)
    )

    # If student, verify they belong to this class
    if is_student and hasattr(request.user, 'student_profile'):
        st = request.user.student_profile
        if lecture.class_room_id != st.current_class_id:
            messages.warning(request, "You can only access lectures for your assigned class.")
            return redirect('lectures:lecture_list')

    return render(request, 'lectures/lecture_detail.html', {
        'lecture': lecture,
        'is_student': is_student,
        'can_manage_lectures': can_manage_lectures,
        'page_title': f"{lecture.subject.name}: {lecture.topic}"
    })


@login_required
@teacher_required
def lecture_create_view(request):
    """Teacher records a daily lecture with voice/audio recording, notes, and homework."""
    if request.method == 'POST':
        form = DailyLectureForm(request.POST, request.FILES)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.teacher = request.user
            lecture.save()

            has_audio = "with Audio Recording" if lecture.audio_recording else ""
            ActivityLog.log_activity(
                request.user, 'CREATE', 'Lectures',
                f"Recorded lecture '{lecture.topic}' for {lecture.class_room.name} ({lecture.subject.name}) {has_audio}",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Class lecture on '{lecture.topic}' recorded successfully!")
            return redirect('lectures:lecture_list')
    else:
        current_date = timezone.now().date()
        form = DailyLectureForm(initial={'date': current_date})

    return render(request, 'lectures/lecture_form.html', {
        'form': form,
        'is_edit': False,
        'page_title': 'Record Class Lecture & Audio'
    })


@login_required
@teacher_required
def lecture_edit_view(request, pk):
    """Teacher edits existing lecture."""
    lecture = get_object_or_404(DailyLecture, pk=pk)
    if request.method == 'POST':
        form = DailyLectureForm(request.POST, request.FILES, instance=lecture)
        if form.is_valid():
            form.save()
            ActivityLog.log_activity(
                request.user, 'UPDATE', 'Lectures',
                f"Updated lecture '{lecture.topic}' for {lecture.class_room.name}",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Lecture '{lecture.topic}' updated successfully!")
            return redirect('lectures:lecture_list')
    else:
        form = DailyLectureForm(instance=lecture)

    return render(request, 'lectures/lecture_form.html', {
        'form': form,
        'lecture': lecture,
        'is_edit': True,
        'page_title': f"Edit Lecture: {lecture.topic}"
    })


@login_required
@teacher_required
def lecture_delete_view(request, pk):
    """Teacher deletes a lecture record."""
    lecture = get_object_or_404(DailyLecture, pk=pk)
    if request.method == 'POST':
        topic = lecture.topic
        cls_name = lecture.class_room.name
        lecture.delete()
        ActivityLog.log_activity(
            request.user, 'DELETE', 'Lectures',
            f"Deleted lecture '{topic}' for {cls_name}",
            request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Lecture '{topic}' deleted successfully.")
    return redirect('lectures:lecture_list')


# -------------------------------------------------------------
# HOMEWORK & DIGITAL DIARY
# -------------------------------------------------------------

@login_required
def homework_list_view(request):
    homeworks = Homework.objects.select_related('class_room', 'section', 'subject', 'teacher').all()
    
    if getattr(request.user, 'is_student', False) and hasattr(request.user, 'student_profile'):
        st = request.user.student_profile
        homeworks = homeworks.filter(class_room=st.current_class, section=st.current_section)
    else:
        class_id = request.GET.get('class_id')
        if class_id:
            homeworks = homeworks.filter(class_room_id=class_id)

    classes = ClassRoom.objects.all()

    return render(request, 'lectures/homework_list.html', {
        'homeworks': homeworks,
        'classes': classes,
        'page_title': 'Homework & Class Diary'
    })


@login_required
@teacher_required
def homework_create_view(request):
    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        if form.is_valid():
            hw = form.save(commit=False)
            hw.teacher = request.user
            hw.save()

            ActivityLog.log_activity(
                request.user, 'CREATE', 'Lectures',
                f"Assigned homework '{hw.title}' to {hw.class_room.name}",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, "Homework assigned successfully!")
            return redirect('lectures:homework_list')
    else:
        form = HomeworkForm()

    return render(request, 'lectures/homework_form.html', {
        'form': form,
        'page_title': 'Assign New Homework'
    })


@login_required
def homework_detail_view(request, pk):
    """View homework instructions and manage submitted digital notebooks."""
    homework = get_object_or_404(Homework.objects.select_related('class_room', 'section', 'subject', 'teacher'), pk=pk)
    submissions = HomeworkSubmission.objects.filter(homework=homework).select_related('student', 'evaluated_by')
    students = Student.objects.filter(current_class=homework.class_room, current_section=homework.section, status='ACTIVE')

    return render(request, 'lectures/homework_detail.html', {
        'homework': homework,
        'submissions': submissions,
        'students': students,
        'page_title': f"Homework: {homework.title}"
    })


@login_required
def submit_homework_action(request, homework_id):
    """Upload completed digital homework task for student."""
    homework = get_object_or_404(Homework, id=homework_id)
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        text = request.POST.get('submission_text', '')
        file_obj = request.FILES.get('submission_file')

        student = get_object_or_404(Student, id=student_id)
        sub, created = HomeworkSubmission.objects.update_or_create(
            homework=homework,
            student=student,
            defaults={
                'submission_text': text,
                'status': HomeworkSubmission.Status.SUBMITTED,
                'submitted_at': timezone.now()
            }
        )
        if file_obj:
            sub.submission_file = file_obj
            sub.save()

        messages.success(request, f"Homework submission for {student.get_full_name()} uploaded successfully!")
    return redirect('lectures:homework_detail', pk=homework_id)


@login_required
@teacher_required
def evaluate_submission_action(request, submission_id):
    """Teacher evaluates student homework, awards marks & comments."""
    sub = get_object_or_404(HomeworkSubmission, id=submission_id)
    if request.method == 'POST':
        marks = request.POST.get('obtained_marks')
        feedback = request.POST.get('teacher_feedback', '')
        status = request.POST.get('status', HomeworkSubmission.Status.EVALUATED)

        sub.obtained_marks = marks if marks else None
        sub.teacher_feedback = feedback
        sub.status = status
        sub.evaluated_by = request.user
        sub.evaluated_at = timezone.now()
        sub.save()

        messages.success(request, f"Evaluation saved for {sub.student.get_full_name()}!")
    return redirect('lectures:homework_detail', pk=sub.homework.id)
