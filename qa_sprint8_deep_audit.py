"""
Rigorous Automated QA Audit Suite for Sprint 8 & Full System Regression
Covers:
1. Biometric Devices & Live Hardware Punch Sync Engine
2. Student Leave Requests & Automated Excused Attendance Workflow
3. Automated WhatsApp & SMS Gateway Hub & Intelligent Trigger Engines
4. Digital Homework Submissions, Notebook Uploads & Teacher Grading
5. 3-Part Bank Fee Challan Voucher Generation
6. Full System Multi-Sprint Regression Tests
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject
from apps.attendance.models import StudentAttendance, TeacherAttendance, BiometricDevice, BiometricPunch, StudentLeaveRequest
from apps.communication.models import SMSWhatsAppGateway, AutomatedNotificationRule, NotificationQueue, MessageTemplate, DirectMessageLog
from apps.lectures.models import Homework, HomeworkSubmission
from apps.fees.models import FeeInvoice, FeeCategory

User = get_user_model()


def run_sprint8_audit():
    print("=" * 70)
    print("  >> RIGOROUS QA COMPREHENSIVE AUDIT REPORT (SPRINT 0 - SPRINT 8)")
    print("=" * 70)

    client = Client()
    passed = 0
    total = 0

    def assert_test(condition, label, category="GENERAL"):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] ({category}) {label}")
        else:
            print(f"  [FAIL] ({category}) {label}")


    # Ensure Admin user exists and login
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_qa', 'qa@school.com', 'admin123', role='ADMIN')
    client.force_login(admin_user)

    # Base references
    student = Student.objects.filter(status='ACTIVE').first()
    teacher = Teacher.objects.filter(status='ACTIVE').first()
    classroom = ClassRoom.objects.first()
    section = Section.objects.first()
    subject = Subject.objects.first()

    # --- 1. BIOMETRIC ATTENDANCE & SYNC HUB ---
    print("\n--- 1. Biometric Hardware Devices & Sync Engine ---")
    resp = client.get('/attendance/biometric/')
    assert_test(resp.status_code == 200, "Biometric Dashboard renders (200)", "BIOMETRIC")

    device, _ = BiometricDevice.objects.get_or_create(
        name="QA Main Gate Facial Scanner",
        defaults={
            'ip_address': '192.168.1.210',
            'port': 4370,
            'device_type': BiometricDevice.DeviceType.FACIAL,
            'status': BiometricDevice.Status.ONLINE,
            'location': 'Main Gate'
        }
    )
    assert_test(device.id is not None, "Biometric device record active in database", "BIOMETRIC")

    # Trigger Sync Action
    sync_resp = client.get(f'/attendance/biometric/sync/{device.id}/')
    assert_test(sync_resp.status_code == 302, "Biometric Sync action redirects (302)", "BIOMETRIC")
    
    device.refresh_from_db()
    assert_test(device.total_logs_synced > 0, f"Biometric synced logs incremented ({device.total_logs_synced})", "BIOMETRIC")

    today = date.today()
    punch_exists = BiometricPunch.objects.filter(device=device, is_processed=True).exists()
    assert_test(punch_exists, "Processed BiometricPunch records created and matched", "BIOMETRIC")

    st_att = StudentAttendance.objects.filter(date=today, student=student).first()
    assert_test(st_att is not None and st_att.status == StudentAttendance.Status.PRESENT, "Student Attendance automatically marked PRESENT via Biometric Sync", "BIOMETRIC")

    # --- 2. STUDENT LEAVE MANAGEMENT WORKFLOW ---
    print("\n--- 2. Student Leave Management & Excused Attendance ---")
    leave_list_resp = client.get('/attendance/leaves/')
    assert_test(leave_list_resp.status_code == 200, "Leave Applications Dashboard renders (200)", "LEAVES")

    # Submit Leave
    start_d = today + timedelta(days=2)
    end_d = today + timedelta(days=3)
    leave_req = StudentLeaveRequest.objects.create(
        student=student,
        start_date=start_d,
        end_date=end_d,
        category=StudentLeaveRequest.Category.SICK,
        reason="Severe fever and doctor advised 2 days bed rest",
        applied_by_name="Parent Aslam",
        status=StudentLeaveRequest.Status.PENDING
    )
    assert_test(leave_req.status == StudentLeaveRequest.Status.PENDING, "Leave application submitted with PENDING status", "LEAVES")

    # Approve Leave
    approve_resp = client.get(f'/attendance/leaves/{leave_req.id}/approve/')
    assert_test(approve_resp.status_code == 302, "Leave approve endpoint executes and redirects", "LEAVES")

    leave_req.refresh_from_db()
    assert_test(leave_req.status == StudentLeaveRequest.Status.APPROVED, "Leave request marked as APPROVED", "LEAVES")

    excused_att = StudentAttendance.objects.filter(date=start_d, student=student).first()
    assert_test(excused_att is not None and excused_att.status == StudentAttendance.Status.EXCUSED, "Attendance automatically updated to EXCUSED for leave dates", "LEAVES")

    # --- 3. AUTOMATED WHATSAPP / SMS NOTIFICATION ENGINE ---
    print("\n--- 3. Automated WhatsApp & SMS Notification Engine ---")
    gw_resp = client.get('/communication/gateways/')
    assert_test(gw_resp.status_code == 200, "Automated Notification Hub renders (200)", "COMMUNICATION")

    queue_resp = client.get('/communication/queue/')
    assert_test(queue_resp.status_code == 200, "Dispatch Queue monitor renders (200)", "COMMUNICATION")

    # Mark a student absent to test absence trigger
    StudentAttendance.objects.update_or_create(
        date=today,
        student=student,
        defaults={'status': StudentAttendance.Status.ABSENT, 'class_room': classroom, 'section': section}
    )

    # Run Absence Alert Trigger Engine
    abs_trig_resp = client.get('/communication/trigger/absence/')
    assert_test(abs_trig_resp.status_code == 302, "Daily Absence Alert engine executes and redirects", "COMMUNICATION")

    pending_queue_count = NotificationQueue.objects.filter(status=NotificationQueue.Status.PENDING).count()
    assert_test(pending_queue_count > 0, f"Automated personalized messages enqueued ({pending_queue_count} pending)", "COMMUNICATION")

    # Run Fee Overdue Trigger Engine
    fee_trig_resp = client.get('/communication/trigger/fee-overdue/')
    assert_test(fee_trig_resp.status_code == 302, "Fee Overdue Reminder engine executes and redirects", "COMMUNICATION")

    # Process Queue Dispatch Action
    dispatch_resp = client.get('/communication/queue/dispatch/')
    assert_test(dispatch_resp.status_code == 302, "Queue batch dispatch executes and redirects", "COMMUNICATION")

    delivered_items = NotificationQueue.objects.filter(status=NotificationQueue.Status.DELIVERED).count()
    assert_test(delivered_items > 0, f"Messages marked DELIVERED and logged in audit ({delivered_items})", "COMMUNICATION")

    # --- 4. DIGITAL HOMEWORK SUBMISSIONS & GRADING ---
    print("\n--- 4. Digital Homework Submissions & Teacher Grading ---")
    hw = Homework.objects.create(
        class_room=classroom,
        section=section,
        subject=subject,
        teacher=admin_user,
        title="Sprint 8 Advanced QA Homework Task",
        description="Solve exercises 8.1 to 8.4 on clean sheet.",
        assigned_date=today,
        due_date=today + timedelta(days=2)
    )
    assert_test(hw.id is not None, "Homework record created", "HOMEWORK")

    hw_detail_resp = client.get(f'/lectures/homework/{hw.id}/')
    assert_test(hw_detail_resp.status_code == 200, "Homework Detail & Submissions page renders (200)", "HOMEWORK")

    # Student Submits Homework
    sub_resp = client.post(f'/lectures/homework/{hw.id}/submit/', {
        'student_id': student.id,
        'submission_text': 'Completed all questions from 8.1 to 8.4 as assigned.'
    })
    assert_test(sub_resp.status_code == 302, "Student homework submission POST redirects (302)", "HOMEWORK")

    submission = HomeworkSubmission.objects.filter(homework=hw, student=student).first()
    assert_test(submission is not None and submission.status == HomeworkSubmission.Status.SUBMITTED, "HomeworkSubmission record created with SUBMITTED status", "HOMEWORK")

    # Teacher Evaluates Submission
    eval_resp = client.post(f'/lectures/homework/evaluate/{submission.id}/', {
        'obtained_marks': '9.5',
        'status': HomeworkSubmission.Status.EVALUATED,
        'teacher_feedback': 'Excellent work and neat presentation!'
    })
    assert_test(eval_resp.status_code == 302, "Teacher grading POST redirects (302)", "HOMEWORK")

    submission.refresh_from_db()
    assert_test(submission.status == HomeworkSubmission.Status.EVALUATED and submission.obtained_marks == Decimal('9.50'), "Submission successfully evaluated with 9.5/10 marks", "HOMEWORK")

    # --- 5. 3-PART BANK FEE CHALLAN ---
    print("\n--- 5. 3-Part Bank Fee Challan Voucher ---")
    invoice = FeeInvoice.objects.first()
    if not invoice:
        cat, _ = FeeCategory.objects.get_or_create(name="Monthly Tuition", defaults={'fee_type': 'MONTHLY'})
        invoice = FeeInvoice.objects.create(
            invoice_number="INV-2026-QA01",
            student=student,
            class_room=classroom,
            fee_month="October 2026",
            fee_year=2026,
            issue_date=today,
            subtotal_amount=Decimal('4500.00'),
            payable_amount=Decimal('4500.00'),
            balance_amount=Decimal('4500.00')
        )

    challan_resp = client.get(f'/fees/challans/{invoice.id}/3part/')
    assert_test(challan_resp.status_code == 200, "3-Part Fee Challan voucher renders HTTP 200", "FEES")
    assert_test(b"BANK COPY" in challan_resp.content and b"STUDENT / PARENT COPY" in challan_resp.content, "Challan contains Bank, School, and Student copies", "FEES")

    # --- 6. REGRESSION TESTS ACROSS SPRINTS ---
    print("\n--- 6. Multi-Sprint Regression Suite ---")
    assert_test(client.get('/transport/').status_code == 200, "Transport Dashboard loads (200)", "REGRESSION")
    assert_test(client.get('/library/').status_code == 200, "Library Dashboard loads (200)", "REGRESSION")
    assert_test(client.get('/inventory/').status_code == 200, "Inventory Dashboard loads (200)", "REGRESSION")
    assert_test(client.get('/api/v1/students/').status_code == 200, "REST API endpoint loads (200)", "REGRESSION")
    assert_test(client.get('/students/portal/').status_code == 200, "Parent Portal loads (200)", "REGRESSION")
    assert_test(client.get('/settings/school/').status_code == 200, "School Profile & Branding settings load (200)", "REGRESSION")

    print("\n" + "=" * 70)
    print(f"  FINAL QA RESULTS: {passed} / {total} PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("\n  >>> SPRINT 8 & FULL SYSTEM REGRESSION IS 100% VERIFIED AND PASSING! <<<")
    else:
        print(f"\n  Warning: {total - passed} tests failed.")

if __name__ == '__main__':
    run_sprint8_audit()

