from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import coordinator_required
from apps.core.models import ActivityLog
from apps.academics.models import ClassRoom, Subject
from .models import SyllabusChapter, SyllabusTopic
from .forms import SyllabusChapterForm, SyllabusTopicForm


@login_required
def syllabus_tracker_view(request):
    classes = ClassRoom.objects.all()
    subjects = Subject.objects.all()

    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')

    selected_class = None
    selected_subject = None
    chapters = []

    if class_id and subject_id:
        selected_class = ClassRoom.objects.filter(id=class_id).first()
        selected_subject = Subject.objects.filter(id=subject_id).first()
        chapters = SyllabusChapter.objects.filter(
            class_room=selected_class,
            subject=selected_subject
        ).prefetch_related('topics')

    # Status update quick action
    if request.method == 'POST' and 'update_topic_status' in request.POST:
        topic_id = request.POST.get('topic_id')
        new_status = request.POST.get('new_status')
        topic = get_object_or_404(SyllabusTopic, id=topic_id)
        topic.status = new_status
        topic.save()
        messages.success(request, f"Updated status for {topic.title} to {topic.get_status_display()}!")
        return redirect(f"{request.path}?class_id={class_id}&subject_id={subject_id}")

    chapter_form = SyllabusChapterForm()
    topic_form = SyllabusTopicForm()

    return render(request, 'syllabus/syllabus_tracker.html', {
        'classes': classes,
        'subjects': subjects,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'chapters': chapters,
        'chapter_form': chapter_form,
        'topic_form': topic_form,
        'page_title': 'Syllabus & Curriculum Tracker'
    })


@login_required
@coordinator_required
def chapter_create_view(request):
    if request.method == 'POST':
        form = SyllabusChapterForm(request.POST)
        if form.is_valid():
            ch = form.save()
            messages.success(request, f"Chapter '{ch.title}' added successfully!")
            return redirect(f"/syllabus/?class_id={ch.class_room.id}&subject_id={ch.subject.id}")
    return redirect('syllabus:tracker')


@login_required
@coordinator_required
def topic_create_view(request):
    if request.method == 'POST':
        form = SyllabusTopicForm(request.POST)
        if form.is_valid():
            top = form.save()
            messages.success(request, f"Topic '{top.title}' added successfully!")
            ch = top.chapter
            return redirect(f"/syllabus/?class_id={ch.class_room.id}&subject_id={ch.subject.id}")
    return redirect('syllabus:tracker')
