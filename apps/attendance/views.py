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
