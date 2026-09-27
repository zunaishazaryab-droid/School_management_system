from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import teacher_required
from apps.core.models import ActivityLog
from apps.academics.models import ClassRoom, Subject
from .models import DailyLecture, Homework
from .forms import DailyLectureForm, HomeworkForm


@login_required
@teacher_required
def lecture_list_view(request):
    lectures = DailyLecture.objects.select_related('class_room', 'section', 'subject', 'teacher').all()

    class_id = request.GET.get('class_id')
    if class_id:
        lectures = lectures.filter(class_room_id=class_id)

    subject_id = request.GET.get('subject_id')
    if subject_id:
        lectures = lectures.filter(subject_id=subject_id)

    date_filter = request.GET.get('date')
    if date_filter:
        lectures = lectures.filter(date=date_filter)

    classes = ClassRoom.objects.all()
    subjects = Subject.objects.all()

    return render(request, 'lectures/lecture_list.html', {
        'lectures': lectures,
        'classes': classes,
        'subjects': subjects,
        'page_title': 'Daily Lecture Records'
    })


@login_required
@teacher_required
def lecture_create_view(request):
    if request.method == 'POST':
        form = DailyLectureForm(request.POST)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.teacher = request.user
            lecture.save()

            ActivityLog.log_activity(
                request.user, 'CREATE', 'Lectures',
                f"Recorded lecture on '{lecture.topic}' for {lecture.class_room.name} ({lecture.subject.name})",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, "Daily lecture log saved successfully!")
            return redirect('lectures:lecture_list')
    else:
        form = DailyLectureForm()

    return render(request, 'lectures/lecture_form.html', {
        'form': form,
        'page_title': 'Record Daily Lecture'
    })


@login_required
def homework_list_view(request):
    homeworks = Homework.objects.select_related('class_room', 'section', 'subject', 'teacher').all()
    
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
