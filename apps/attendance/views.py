from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date, datetime
from apps.accounts.decorators import teacher_required, coordinator_required
from apps.core.models import ActivityLog
from apps.academics.models import ClassRoom, Section
from apps.students.models import Student
from apps.teachers.models import Teacher
from .models import StudentAttendance, TeacherAttendance


@login_required
@teacher_required
def student_attendance_view(request):
    classes = ClassRoom.objects.all()
    
    # Filter parameters
    selected_date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    class_id = request.GET.get('class_id')
    section_id = request.GET.get('section_id')

    try:
        attendance_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        attendance_date = date.today()

    sections = []
    students_data = []
    selected_class = None
    selected_section = None

    if class_id:
        selected_class = ClassRoom.objects.filter(id=class_id).first()
        sections = Section.objects.filter(class_room_id=class_id)
        if not section_id and sections.exists():
            section_id = sections.first().id

    if section_id:
        selected_section = Section.objects.filter(id=section_id).first()

    if selected_class and selected_section:
        # Load students in section
        students = Student.objects.filter(
            current_class=selected_class,
            current_section=selected_section,
            status='ACTIVE'
        ).order_by('roll_number', 'first_name')

        # Load existing attendance for this date
        existing_records = {
            att.student_id: att
            for att in StudentAttendance.objects.filter(
                date=attendance_date,
                class_room=selected_class,
                section=selected_section
            )
        }

        for st in students:
            att = existing_records.get(st.id)
            students_data.append({
                'student': st,
                'status': att.status if att else 'PRESENT',
                'remarks': att.remarks if att else ''
            })

    # Save attendance POST
    if request.method == 'POST' and selected_class and selected_section:
        saved_count = 0
        for item in students_data:
            st = item['student']
            status_val = request.POST.get(f'status_{st.id}', 'PRESENT')
            remarks_val = request.POST.get(f'remarks_{st.id}', '')

            StudentAttendance.objects.update_or_create(
                date=attendance_date,
                student=st,
                defaults={
                    'class_room': selected_class,
                    'section': selected_section,
                    'status': status_val,
                    'remarks': remarks_val,
                    'recorded_by': request.user
                }
            )
            saved_count += 1

        ActivityLog.log_activity(
            request.user, 'CREATE', 'Attendance',
            f"Marked attendance for {saved_count} students in {selected_class.name} - Sec {selected_section.name} on {attendance_date}",
            request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f"Attendance saved successfully for {saved_count} students on {attendance_date}!")
        return redirect(f"{request.path}?date={selected_date_str}&class_id={class_id}&section_id={section_id}")

    return render(request, 'attendance/student_attendance.html', {
        'classes': classes,
        'sections': sections,
        'students_data': students_data,
        'selected_date': selected_date_str,
        'selected_class': selected_class,
        'selected_section': selected_section,
        'page_title': 'Student Daily Attendance Register'
    })


@login_required
@coordinator_required
def teacher_attendance_view(request):
    selected_date_str = request.GET.get('date', date.today().strftime('%Y-%m-%d'))
    try:
        attendance_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        attendance_date = date.today()

    teachers = Teacher.objects.filter(status='ACTIVE').select_related('user')
    existing_records = {
        att.teacher_id: att
        for att in TeacherAttendance.objects.filter(date=attendance_date)
    }

    teacher_data = []
    for t in teachers:
        att = existing_records.get(t.id)
        teacher_data.append({
            'teacher': t,
            'status': att.status if att else 'PRESENT',
            'check_in': att.check_in_time if att else '',
            'remarks': att.remarks if att else ''
        })

    if request.method == 'POST':
        for item in teacher_data:
            t = item['teacher']
            status_val = request.POST.get(f'status_{t.id}', 'PRESENT')
            remarks_val = request.POST.get(f'remarks_{t.id}', '')

            TeacherAttendance.objects.update_or_create(
                date=attendance_date,
                teacher=t,
                defaults={
                    'status': status_val,
                    'remarks': remarks_val,
                    'recorded_by': request.user
                }
            )

        messages.success(request, f"Faculty attendance saved successfully for {attendance_date}!")
        return redirect(f"{request.path}?date={selected_date_str}")

    return render(request, 'attendance/teacher_attendance.html', {
        'teacher_data': teacher_data,
        'selected_date': selected_date_str,
        'page_title': 'Faculty Attendance Register'
    })


@login_required
def attendance_report_view(request):
    classes = ClassRoom.objects.all()
    selected_class_id = request.GET.get('class_id')
    
    report_data = []
    if selected_class_id:
        students = Student.objects.filter(current_class_id=selected_class_id, status='ACTIVE')
        for st in students:
            total_days = st.attendance_records.count()
            present_days = st.attendance_records.filter(status__in=['PRESENT', 'LATE']).count()
            pct = int((present_days / total_days * 100)) if total_days > 0 else 100
            report_data.append({
                'student': st,
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': total_days - present_days,
                'percentage': pct
            })

    return render(request, 'attendance/attendance_report.html', {
        'classes': classes,
        'selected_class_id': int(selected_class_id) if selected_class_id else None,
        'report_data': report_data,
        'page_title': 'Monthly Attendance Summary'
    })


from django.utils import timezone
from .models import BiometricDevice, BiometricPunch, StudentLeaveRequest


@login_required
def biometric_dashboard_view(request):
    """Hub for managing biometric machines and viewing live punch stream."""
    devices = BiometricDevice.objects.all()
    if not devices.exists():
        BiometricDevice.objects.create(
            name="Main Entrance Turnstile Terminal #1",
            device_type=BiometricDevice.DeviceType.HYBRID,
            ip_address="192.168.1.201",
            port=4370,
            location="Main School Gate",
            status=BiometricDevice.Status.ONLINE,
            total_logs_synced=142
        )
        BiometricDevice.objects.create(
            name="Staff Room Facial Scanner #2",
            device_type=BiometricDevice.DeviceType.FACIAL,
            ip_address="192.168.1.202",
            port=4370,
            location="Faculty Administration Block",
            status=BiometricDevice.Status.ONLINE,
            total_logs_synced=68
        )
        devices = BiometricDevice.objects.all()

    today = date.today()
    recent_punches = BiometricPunch.objects.select_related('device', 'matched_student', 'matched_teacher')[:40]
    
    total_punches_today = BiometricPunch.objects.filter(timestamp__date=today).count()
    unprocessed_count = BiometricPunch.objects.filter(is_processed=False).count()

    if request.method == 'POST' and 'add_device' in request.POST:
        name = request.POST.get('name')
        ip = request.POST.get('ip_address', '192.168.1.203')
        port = int(request.POST.get('port', 4370))
        loc = request.POST.get('location', 'Campus')
        dtype = request.POST.get('device_type', BiometricDevice.DeviceType.FINGERPRINT)
        BiometricDevice.objects.create(
            name=name, ip_address=ip, port=port, location=loc, device_type=dtype, status=BiometricDevice.Status.ONLINE
        )
        messages.success(request, f"Biometric device '{name}' added successfully!")
        return redirect('attendance:biometric_dashboard')

    return render(request, 'attendance/biometric_dashboard.html', {
        'devices': devices,
        'recent_punches': recent_punches,
        'total_punches_today': total_punches_today,
        'unprocessed_count': unprocessed_count,
        'page_title': 'Biometric Attendance & Device Sync Hub'
    })


@login_required
def biometric_sync_action_view(request, device_id):
    """Simulates real-time synchronization from hardware device & marks attendance."""
    device = BiometricDevice.objects.get(id=device_id)
    today = date.today()
    now_time = timezone.now()

    # Get active students & teachers
    students = Student.objects.filter(status='ACTIVE')
    teachers = Teacher.objects.filter(status='ACTIVE')

    synced_count = 0
    # Simulate punches for students
    for st in students:
        punch_dt = timezone.make_aware(datetime.combine(today, datetime.strptime("07:48:00", "%H:%M:%S").time()))
        punch, created = BiometricPunch.objects.get_or_create(
            device=device,
            biometric_user_id=st.admission_number,
            timestamp=punch_dt,
            defaults={
                'punch_type': BiometricPunch.PunchType.CHECK_IN,
                'matched_student': st,
                'is_processed': True,
                'notes': 'Auto-synced via ZKTeco TCP/IP Stream'
            }
        )
        # Update Student Attendance record
        StudentAttendance.objects.update_or_create(
            date=today,
            student=st,
            defaults={
                'class_room': st.current_class,
                'section': st.current_section,
                'status': StudentAttendance.Status.PRESENT,
                'remarks': f"Biometric Punch @ {punch_dt.strftime('%H:%M:%S')} via {device.name}",
                'recorded_by': request.user
            }
        )
        synced_count += 1

    # Simulate punches for teachers
    for tch in teachers:
        t_punch_dt = timezone.make_aware(datetime.combine(today, datetime.strptime("07:42:00", "%H:%M:%S").time()))
        BiometricPunch.objects.get_or_create(
            device=device,
            biometric_user_id=tch.employee_id,
            timestamp=t_punch_dt,
            defaults={
                'punch_type': BiometricPunch.PunchType.CHECK_IN,
                'matched_teacher': tch,
                'is_processed': True,
                'notes': 'Facial recognition match'
            }
        )
        TeacherAttendance.objects.update_or_create(
            date=today,
            teacher=tch,
            defaults={
                'status': TeacherAttendance.Status.PRESENT,
                'check_in_time': t_punch_dt.time(),
                'remarks': f"Facial Scanner @ {device.name}",
                'recorded_by': request.user
            }
        )
        synced_count += 1

    device.last_sync_time = now_time
    device.total_logs_synced += synced_count
    device.status = BiometricDevice.Status.ONLINE
    device.save()

    ActivityLog.log_activity(
        request.user, 'CREATE', 'Attendance',
        f"Synchronized {synced_count} biometric logs from '{device.name}' and updated daily registers.",
        request.META.get('REMOTE_ADDR')
    )

    messages.success(request, f"Successfully synced {synced_count} biometric logs from '{device.name}'! Registers updated.")
    return redirect('attendance:biometric_dashboard')


@login_required
def leave_request_list_view(request):
    """Admin / Teacher portal view for reviewing student leave requests."""
    status_filter = request.GET.get('status', 'ALL')
    leaves = StudentLeaveRequest.objects.select_related('student', 'student__current_class', 'student__current_section', 'reviewed_by')

    if status_filter in ['PENDING', 'APPROVED', 'REJECTED']:
        leaves = leaves.filter(status=status_filter)

    pending_count = StudentLeaveRequest.objects.filter(status='PENDING').count()
    approved_count = StudentLeaveRequest.objects.filter(status='APPROVED').count()

    return render(request, 'attendance/leave_requests_list.html', {
        'leaves': leaves,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'page_title': 'Student Leave Applications & Approvals'
    })


@login_required
def process_leave_request_view(request, leave_id, action):
    """Approve or Reject student leave and auto-excuse attendance."""
    leave = StudentLeaveRequest.objects.get(id=leave_id)
    remarks = request.POST.get('remarks', request.GET.get('remarks', ''))

    if action == 'approve':
        leave.status = StudentLeaveRequest.Status.APPROVED
        leave.admin_remarks = remarks or "Approved by administration"
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.save()

        # Update attendance for the leave date range
        cur_date = leave.start_date
        while cur_date <= leave.end_date:
            StudentAttendance.objects.update_or_create(
                date=cur_date,
                student=leave.student,
                defaults={
                    'class_room': leave.student.current_class,
                    'section': leave.student.current_section,
                    'status': StudentAttendance.Status.EXCUSED,
                    'remarks': f"Official Leave Approved (#{leave.id}) - {leave.get_category_display()}",
                    'recorded_by': request.user
                }
            )
            cur_date += timezone.timedelta(days=1)

        messages.success(request, f"Leave application #{leave.id} for {leave.student.get_full_name()} approved! Attendance marked as Excused.")
    elif action == 'reject':
        leave.status = StudentLeaveRequest.Status.REJECTED
        leave.admin_remarks = remarks or "Rejected by administration"
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.save()
        messages.warning(request, f"Leave application #{leave.id} for {leave.student.get_full_name()} rejected.")

    return redirect('attendance:leave_list')


@login_required
def submit_leave_request_view(request):
    """Student / Parent application form for applying for leaves."""
    students = Student.objects.filter(status='ACTIVE')
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        category = request.POST.get('category', StudentLeaveRequest.Category.CASUAL)
        reason = request.POST.get('reason')
        applied_by = request.POST.get('applied_by_name', request.user.get_full_name() or request.user.username)
        doc = request.FILES.get('document')

        student = Student.objects.get(id=student_id)
        req = StudentLeaveRequest.objects.create(
            student=student,
            start_date=start_date,
            end_date=end_date,
            category=category,
            reason=reason,
            applied_by_name=applied_by,
            document=doc
        )
        messages.success(request, f"Leave application for {student.get_full_name()} submitted successfully! Reference #{req.id}")
        return redirect('attendance:leave_list')

    return render(request, 'attendance/submit_leave.html', {
        'students': students,
        'today': date.today().strftime('%Y-%m-%d'),
        'page_title': 'Submit Online Leave Application'
    })

