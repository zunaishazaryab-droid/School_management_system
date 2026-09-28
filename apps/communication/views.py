import urllib.parse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from apps.accounts.decorators import coordinator_required
from apps.core.models import ActivityLog
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academics.models import ClassRoom, Section
from .models import Announcement, MessageTemplate, DirectMessageLog
from .forms import AnnouncementForm, MessageTemplateForm, DirectMessageSendForm


@login_required
def announcement_list_view(request):
    """Notice board of all active and historical circulars"""
    query = request.GET.get('q', '').strip()
    audience_filter = request.GET.get('audience', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    status_filter = request.GET.get('status', 'active').strip()

    announcements = Announcement.objects.select_related('target_class', 'target_section', 'author').all()

    if query:
        announcements = announcements.filter(Q(title__icontains=query) | Q(content__icontains=query))

    if audience_filter:
        announcements = announcements.filter(audience=audience_filter)

    if priority_filter:
        announcements = announcements.filter(priority=priority_filter)

    today = timezone.now().date()
    if status_filter == 'active':
        announcements = announcements.filter(
            is_published=True,
            publish_date__lte=today
        ).filter(Q(expiry_date__isnull=True) | Q(expiry_date__gte=today))
    elif status_filter == 'draft':
        announcements = announcements.filter(is_published=False)
    elif status_filter == 'expired':
        announcements = announcements.filter(expiry_date__lt=today)

    total_active = Announcement.objects.filter(is_published=True, publish_date__lte=today).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    ).count()

    context = {
        'page_title': 'Notice Board & Circulars',
        'announcements': announcements,
        'total_active': total_active,
        'query': query,
        'audience_filter': audience_filter,
        'priority_filter': priority_filter,
        'status_filter': status_filter,
        'audiences': Announcement.Audience.choices,
        'priorities': Announcement.Priority.choices,
    }
    return render(request, 'communication/announcement_list.html', context)


@login_required
@coordinator_required
def announcement_create_view(request):
    """Create a new circular notice"""
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.author = request.user
            ann.save()

            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Communication',
                description=f"Published announcement: '{ann.title}' ({ann.get_audience_display()}).",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Announcement '{ann.title}' published successfully!")
            return redirect('communication:announcement_detail', pk=ann.pk)
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        form = AnnouncementForm(initial={'publish_date': timezone.now().date(), 'is_published': True})

    return render(request, 'communication/announcement_form.html', {
        'page_title': 'Publish New Circular / Announcement',
        'form': form,
        'is_edit': False,
    })


@login_required
@coordinator_required
def announcement_edit_view(request, pk):
    """Edit an existing announcement"""
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, request.FILES, instance=ann)
        if form.is_valid():
            ann = form.save()
            ActivityLog.log_activity(
                user=request.user,
                action='UPDATE',
                module='Communication',
                description=f"Updated announcement: '{ann.title}'.",
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Announcement '{ann.title}' updated successfully!")
            return redirect('communication:announcement_detail', pk=ann.pk)
        else:
            messages.error(request, "Please fix form errors below.")
    else:
        form = AnnouncementForm(instance=ann)

    return render(request, 'communication/announcement_form.html', {
        'page_title': f"Edit Notice: {ann.title}",
        'form': form,
        'announcement': ann,
        'is_edit': True,
    })


@login_required
def announcement_detail_view(request, pk):
    """View full announcement with printable notice sheet"""
    ann = get_object_or_404(
        Announcement.objects.select_related('target_class', 'target_section', 'author'),
        pk=pk
    )
    return render(request, 'communication/announcement_detail.html', {
        'page_title': f"Notice: {ann.title}",
        'announcement': ann,
    })


@login_required
@coordinator_required
def announcement_delete_view(request, pk):
    """Delete an announcement"""
    ann = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        title = ann.title
        ann.delete()
        ActivityLog.log_activity(
            user=request.user,
            action='DELETE',
            module='Communication',
            description=f"Deleted announcement: '{title}'.",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Notice '{title}' deleted.")
        return redirect('communication:announcement_list')
    return redirect('communication:announcement_detail', pk=pk)


@login_required
@coordinator_required
def broadcast_center_view(request):
    """Direct Parent/Teacher SMS & WhatsApp messaging center with variable auto-fill and web link dispatch"""
    students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section')
    teachers = Teacher.objects.filter(is_active=True).select_related('user')
    templates = MessageTemplate.objects.all()
    classes = ClassRoom.objects.all()

    whatsapp_url = None
    generated_message = ""
    target_phone = ""
    target_name = ""

    if request.method == 'POST' and 'send_direct' in request.POST:
        rec_type = request.POST.get('recipient_type', 'STUDENT')
        template_id = request.POST.get('template_id')
        student_id = request.POST.get('student_id')
        teacher_id = request.POST.get('teacher_id')
        custom_phone = request.POST.get('custom_phone', '').strip()
        custom_name = request.POST.get('custom_name', '').strip()
        channel = request.POST.get('channel', 'WHATSAPP')
        raw_message = request.POST.get('message_body', '').strip()

        # Variable replacement context
        template_obj = MessageTemplate.objects.filter(id=template_id).first() if template_id else None
        msg_text = raw_message or (template_obj.body if template_obj else '')

        if rec_type == 'STUDENT' and student_id:
            stu = Student.objects.filter(id=student_id).first()
            if stu:
                target_name = stu.get_full_name()
                target_phone = stu.guardian_phone
                # Dynamic replacements
                msg_text = msg_text.replace('{student_name}', stu.get_full_name())
                msg_text = msg_text.replace('{guardian_name}', stu.guardian_name)
                msg_text = msg_text.replace('{class_name}', f"{stu.current_class.name}-{stu.current_section.name}")
                msg_text = msg_text.replace('{date}', timezone.now().strftime('%d-%b-%Y'))
                msg_text = msg_text.replace('{school_name}', 'Elite Model School')
        elif rec_type == 'TEACHER' and teacher_id:
            tch = Teacher.objects.filter(id=teacher_id).first()
            if tch:
                target_name = tch.user.get_full_name()
                target_phone = tch.phone
                msg_text = msg_text.replace('{teacher_name}', tch.user.get_full_name())
                msg_text = msg_text.replace('{date}', timezone.now().strftime('%d-%b-%Y'))
        else:
            target_name = custom_name or "Recipient"
            target_phone = custom_phone

        # Clean phone for WhatsApp (remove spaces, dashes)
        clean_phone = target_phone.replace('-', '').replace(' ', '').replace('+', '')
        if clean_phone.startswith('0'):
            clean_phone = '92' + clean_phone[1:]

        # Log direct message
        log_entry = DirectMessageLog.objects.create(
            recipient_type=rec_type,
            recipient_name=target_name,
            recipient_phone=target_phone,
            channel=channel,
            template=template_obj,
            message_body=msg_text,
            status='SENT',
            sent_by=request.user
        )

        ActivityLog.log_activity(
            user=request.user,
            action='CREATE',
            module='Communication',
            description=f"Logged {channel} broadcast to {target_name} ({target_phone}).",
            ip_address=request.META.get('REMOTE_ADDR')
        )

        encoded_text = urllib.parse.quote(msg_text)
        whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_text}"
        generated_message = msg_text
        messages.success(request, f"Message prepared for {target_name}! Click the button below to launch WhatsApp or copy.")

    context = {
        'page_title': 'Parent & Faculty Broadcast Center',
        'students': students,
        'teachers': teachers,
        'templates': templates,
        'classes': classes,
        'whatsapp_url': whatsapp_url,
        'generated_message': generated_message,
        'target_phone': target_phone,
        'target_name': target_name,
    }
    return render(request, 'communication/broadcast_center.html', context)


@login_required
@coordinator_required
def template_list_view(request):
    """View and manage reusable SMS / WhatsApp message templates"""
    templates = MessageTemplate.objects.all()
    form = MessageTemplateForm()

    if request.method == 'POST' and 'create_template' in request.POST:
        form = MessageTemplateForm(request.POST)
        if form.is_valid():
            t = form.save()
            messages.success(request, f"Template '{t.title}' created.")
            return redirect('communication:template_list')

    return render(request, 'communication/template_list.html', {
        'page_title': 'Message Templates (SMS / WhatsApp)',
        'templates': templates,
        'form': form,
    })


@login_required
@coordinator_required
def template_delete_view(request, pk):
    """Delete a template"""
    template = get_object_or_404(MessageTemplate, pk=pk)
    if request.method == 'POST':
        title = template.title
        template.delete()
        messages.success(request, f"Template '{title}' deleted.")
    return redirect('communication:template_list')


@login_required
def communication_history_view(request):
    """View log of all dispatched direct messages and alerts"""
    logs = DirectMessageLog.objects.select_related('template', 'sent_by').all()
    channel_filter = request.GET.get('channel', '')
    status_filter = request.GET.get('status', '')

    if channel_filter:
        logs = logs.filter(channel=channel_filter)
    if status_filter:
        logs = logs.filter(status=status_filter)

    return render(request, 'communication/history.html', {
        'page_title': 'Communication & Dispatch History',
        'logs': logs,
        'channel_filter': channel_filter,
        'status_filter': status_filter,
    })
