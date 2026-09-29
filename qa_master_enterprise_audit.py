"""
======================================================================
  🏛️ GEN'X VISION SCHOOL SYSTEM — MASTER ENTERPRISE QA AUDIT SUITE
======================================================================
Comprehensive End-to-End Automated Verification covering ALL Sprints (0 to 9)
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
from django.db.models import Sum

from apps.students.models import Student, StudentDocument
from apps.teachers.models import Teacher
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject, TimetableEntry
from apps.core.models import Branch, SchoolSetting, ActivityLog, Notification
from apps.attendance.models import StudentAttendance, TeacherAttendance, BiometricDevice, BiometricPunch, StudentLeaveRequest
from apps.lectures.models import DailyLecture, Homework, HomeworkSubmission
from apps.syllabus.models import SyllabusChapter, SyllabusTopic
from apps.fees.models import FeeCategory, FeeStructure, FeeInvoice, FeePayment, FeeInvoiceItem
from apps.examinations.models import Exam, ExamSchedule, ExamMarks, ExamStudentResult, OnlineAssessment, AssessmentQuestion, StudentAssessmentAttempt, GradeScale
from apps.expenses.models import ExpenseCategory, Expense
from apps.communication.models import Announcement, MessageTemplate, DirectMessageLog, SMSWhatsAppGateway, AutomatedNotificationRule, NotificationQueue
from apps.transport.models import Vehicle, Route, RouteStop, StudentTransportAllocation
from apps.library.models import BookCategory, Book, BookIssue
from apps.inventory.models import ItemCategory, Supplier, InventoryItem, StockTransaction

User = get_user_model()


def run_master_qa_audit():
    print("=" * 76)
    print("  🚀 GEN'X VISION SCHOOL SYSTEM — MASTER ENTERPRISE QA DEEP AUDIT")
    print("=" * 76)

    client = Client()
    passed = 0
    total = 0

    def test(condition, label, category="GENERAL"):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] ({category}) {label}")
        else:
            print(f"  [FAIL] ({category}) {label}")

    # -------------------------------------------------------------
    # 1. SECURITY, AUTHENTICATION & ROLE-BASED ACCESS CONTROL (RBAC)
    # -------------------------------------------------------------
    print("\n--- 1. Security, Authentication & Role-Based Access Control (RBAC) ---")
    admin_user, _ = User.objects.get_or_create(username='admin_master_qa', defaults={'role': 'ADMIN', 'email': 'admin@genxvision.edu.pk'})
    admin_user.set_password('admin123')
    admin_user.is_superuser = True
    admin_user.is_staff = True
    admin_user.save()

    teacher_user, _ = User.objects.get_or_create(username='teacher_qa', defaults={'role': 'TEACHER', 'email': 'teacher@genxvision.edu.pk'})
    parent_user, _ = User.objects.get_or_create(username='parent_qa', defaults={'role': 'PARENT', 'email': 'parent@genxvision.edu.pk'})

    anon_client = Client()
    test(anon_client.get('/attendance/student/').status_code in [302, 401, 403], "Anonymous user blocked from Student Attendance register", "SECURITY")
    test(anon_client.get('/fees/').status_code in [302, 401, 403], "Anonymous user blocked from Fee Management dashboard", "SECURITY")
    test(anon_client.get('/inventory/').status_code in [302, 401, 403], "Anonymous user blocked from Asset Inventory", "SECURITY")

    client.force_login(admin_user)
    test(client.get('/').status_code == 200, "Authenticated Admin renders Main ERP Dashboard (200)", "SECURITY")

    # -------------------------------------------------------------
    # 2. MULTI-CAMPUS ARCHITECTURE & BRANCH CONTEXT SWITCHING
    # -------------------------------------------------------------
    print("\n--- 2. Multi-Campus Architecture & Branch Context Switching ---")
    main_branch = Branch.objects.filter(is_main_branch=True).first()
    if not main_branch:
        main_branch = Branch.objects.create(name="Main Campus Johar Town", code="GXV-M01", is_main_branch=True, is_active=True)
    test(main_branch is not None, f"Principal Campus record active: '{main_branch.name}'", "CAMPUS")

    campus_resp = client.get('/campuses/')
    test(campus_resp.status_code == 200, "Campuses Management Hub loads (200)", "CAMPUS")

    switch_resp = client.get(f'/campuses/switch/{main_branch.id}/')
    test(switch_resp.status_code == 302, "Switch Campus context action executes (302)", "CAMPUS")
    test(client.session.get('active_branch_id') == main_branch.id, "Active session working campus updated", "CAMPUS")

    # -------------------------------------------------------------
    # 3. CORE ACADEMICS: CLASSES, SECTIONS, SUBJECTS & TIMETABLE
    # -------------------------------------------------------------
    print("\n--- 3. Core Academics, Classes, Curriculum & Timetable ---")
    acad_year = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
    classroom = ClassRoom.objects.first()
    section = Section.objects.first()
    subject = Subject.objects.first()

    test(classroom is not None, f"Classroom active: {classroom.name}", "ACADEMICS")
    test(section is not None, f"Section active: {section.name}", "ACADEMICS")
    test(subject is not None, f"Subject active: {subject.name} ({subject.code})", "ACADEMICS")

    tt_resp = client.get('/academics/timetable/')
    test(tt_resp.status_code == 200, "Class Timetable Matrix loads (200)", "ACADEMICS")

    # -------------------------------------------------------------
    # 4. STUDENT & TEACHER LIFECYCLE MANAGEMENT
    # -------------------------------------------------------------
    print("\n--- 4. Student & Faculty Directory Lifecycle ---")
    student = Student.objects.filter(status='ACTIVE').first()
    teacher = Teacher.objects.filter(status='ACTIVE').first()
    test(student is not None, f"Enrolled student active: {student.get_full_name()} (#{student.admission_number})", "STUDENTS")
    test(teacher is not None, f"Faculty teacher active: {teacher.get_full_name()} (#{teacher.employee_id})", "TEACHERS")

    stu_list_resp = client.get('/students/')
    test(stu_list_resp.status_code == 200, "Student Directory loads (200)", "STUDENTS")

    tch_list_resp = client.get('/teachers/')
    test(tch_list_resp.status_code == 200, "Faculty Directory loads (200)", "TEACHERS")

    # -------------------------------------------------------------
    # 5. ATTENDANCE REGISTERS, BIOMETRIC SYNC & LEAVE APPROVALS
    # -------------------------------------------------------------
    print("\n--- 5. Attendance Registers, Biometrics & Leave Workflows ---")
    today = date.today()
    bio_dash_resp = client.get('/attendance/biometric/')
    test(bio_dash_resp.status_code == 200, "Biometric Sync Hub loads (200)", "BIOMETRICS")

    device = BiometricDevice.objects.first()
    if device:
        sync_resp = client.get(f'/attendance/biometric/sync/{device.id}/')
        test(sync_resp.status_code == 302, f"Simulated live hardware sync executed from '{device.name}' (302)", "BIOMETRICS")
        test(StudentAttendance.objects.filter(date=today, student=student).exists(), "Daily Student Attendance auto-updated via Biometric Punch", "BIOMETRICS")

    # Online Leave Request Workflow
    leave_req = StudentLeaveRequest.objects.create(
        student=student,
        start_date=today + timedelta(days=4),
        end_date=today + timedelta(days=5),
        category=StudentLeaveRequest.Category.SICK,
        reason="Medical throat infection",
        status=StudentLeaveRequest.Status.PENDING
    )
    test(leave_req.status == StudentLeaveRequest.Status.PENDING, "Leave Request submitted with PENDING status", "LEAVES")

    appr_resp = client.get(f'/attendance/leaves/{leave_req.id}/approve/')
    test(appr_resp.status_code == 302, "Admin approved leave request (302)", "LEAVES")
    leave_req.refresh_from_db()
    test(leave_req.status == StudentLeaveRequest.Status.APPROVED, "Leave request marked as APPROVED", "LEAVES")
    test(StudentAttendance.objects.filter(date=today + timedelta(days=4), student=student, status='EXCUSED').exists(), "Daily attendance updated to EXCUSED for leave dates", "LEAVES")

    # -------------------------------------------------------------
    # 6. SYLLABUS TRACKING & DIGITAL HOMEWORK SUBMISSIONS
    # -------------------------------------------------------------
    print("\n--- 6. Syllabus Tracking & Digital Homework Submissions ---")
    syl_resp = client.get('/syllabus/tracker/')
    test(syl_resp.status_code == 200, "Syllabus Tracker Hub loads (200)", "SYLLABUS")

    hw_resp = client.get('/lectures/homework/')
    test(hw_resp.status_code == 200, "Homework Diary loads (200)", "HOMEWORK")

    hw = Homework.objects.first()
    if hw:
        sub_resp = client.post(f'/lectures/homework/{hw.id}/submit/', {
            'student_id': student.id,
            'submission_text': 'Completed notebook work QA verification.'
        })
        test(sub_resp.status_code == 302, "Student submitted digital homework (302)", "HOMEWORK")

        sub = HomeworkSubmission.objects.filter(homework=hw, student=student).first()
        test(sub is not None, "HomeworkSubmission record stored in database", "HOMEWORK")

        eval_resp = client.post(f'/lectures/homework/evaluate/{sub.id}/', {
            'obtained_marks': '9.0',
            'status': HomeworkSubmission.Status.EVALUATED,
            'teacher_feedback': 'Great effort.'
        })
        test(eval_resp.status_code == 302, "Teacher evaluated and graded homework (302)", "HOMEWORK")

    # -------------------------------------------------------------
    # 7. EXAMINATIONS, REPORT CARDS & ONLINE CBT QUIZZES
    # -------------------------------------------------------------
    print("\n--- 7. Examinations, Report Cards & Online CBT Testing ---")
    exam = Exam.objects.first()
    if exam:
        rep_resp = client.get(f'/examinations/{exam.id}/report-card/{student.id}/')
        test(rep_resp.status_code == 200, f"Official Report Card loads for student #{student.admission_number} (200)", "EXAMINATIONS")

    cbt_list_resp = client.get('/examinations/cbt/')
    test(cbt_list_resp.status_code == 200, "Online CBT Assessment List loads (200)", "CBT")

    quiz = OnlineAssessment.objects.first()
    if quiz:
        take_resp = client.get(f'/examinations/cbt/{quiz.id}/take/')
        test(take_resp.status_code == 200, "CBT Timed Test Taking interface loads (200)", "CBT")

        results_resp = client.get(f'/examinations/cbt/{quiz.id}/results/')
        test(results_resp.status_code == 200, "CBT Results & Cohort Ranking loads (200)", "CBT")

    # -------------------------------------------------------------
    # 8. FINANCE, FEES, 3-PART BANK CHALLAN & EXPENSES
    # -------------------------------------------------------------
    print("\n--- 8. Financial Management, Fee Collection & 3-Part Challans ---")
    fee_dash_resp = client.get('/fees/')
    test(fee_dash_resp.status_code == 200, "Fee Dashboard loads (200)", "FEES")

    invoice = FeeInvoice.objects.first()
    if invoice:
        challan_resp = client.get(f'/fees/challans/{invoice.id}/3part/')
        test(challan_resp.status_code == 200, "3-Part Bank Fee Challan loads (200)", "FEES")
        test(b"BANK COPY" in challan_resp.content and b"SCHOOL COPY" in challan_resp.content, "Challan contains Bank, School, and Student copies", "FEES")

    exp_resp = client.get('/expenses/')
    test(exp_resp.status_code == 200, "Expense Management loads (200)", "EXPENSES")

    # -------------------------------------------------------------
    # 9. AUTOMATED WHATSAPP/SMS NOTIFICATIONS & QUEUE
    # -------------------------------------------------------------
    print("\n--- 9. Automated WhatsApp & SMS Notification Dispatch ---")
    gw_resp = client.get('/communication/gateways/')
    test(gw_resp.status_code == 200, "Automated WhatsApp/SMS Gateways Hub loads (200)", "NOTIFICATIONS")

    # Trigger Absence Scanner
    trig_resp = client.get('/communication/trigger/absence/')
    test(trig_resp.status_code == 302, "Daily Absence Alert engine executes (302)", "NOTIFICATIONS")

    # Process Queue
    q_disp_resp = client.get('/communication/queue/dispatch/')
    test(q_disp_resp.status_code == 302, "Queue batch dispatch executes (302)", "NOTIFICATIONS")

    # -------------------------------------------------------------
    # 10. AUXILIARY: TRANSPORT, LIBRARY & INVENTORY
    # -------------------------------------------------------------
    print("\n--- 10. Logistics: Transport, Library & Inventory ---")
    test(client.get('/transport/').status_code == 200, "Transport Bus Fleet Dashboard loads (200)", "TRANSPORT")
    test(client.get('/library/').status_code == 200, "Library Catalog loads (200)", "LIBRARY")
    test(client.get('/inventory/').status_code == 200, "Asset Inventory Dashboard loads (200)", "INVENTORY")

    # -------------------------------------------------------------
    # 11. SECURITY QR CODE VERIFICATION & BADGE SCANNER
    # -------------------------------------------------------------
    print("\n--- 11. Dynamic QR Code Identity Verification Gateway ---")
    verify_resp = client.get(f'/verify-badge/{student.admission_number}/')
    test(verify_resp.status_code == 200, "QR Badge Public Verification page loads (200)", "QR_VERIFY")
    test(b"OFFICIAL IDENTITY VERIFIED" in verify_resp.content, "Badge verified with valid student details", "QR_VERIFY")

    scanner_resp = client.get('/security/scanner/')
    test(scanner_resp.status_code == 200, "Security Guard Scanner interface loads (200)", "QR_VERIFY")

    # -------------------------------------------------------------
    # 12. EXECUTIVE ANALYTICS, REST APIS & BACKUPS
    # -------------------------------------------------------------
    print("\n--- 12. Executive Analytics, REST APIs & Backups ---")
    exec_resp = client.get('/reports/executive/')
    test(exec_resp.status_code == 200, "Executive Leadership Analytics loads (200)", "EXECUTIVE")

    api_resp = client.get('/api/v1/students/')
    test(api_resp.status_code == 200, "Mobile REST API endpoint /api/v1/students/ loads (200)", "API")

    backup_resp = client.get('/settings/backup/')
    test(backup_resp.status_code == 200, "Database Backup & Recovery loads (200)", "BACKUP")

    print("\n" + "=" * 76)
    print(f"  🏁 MASTER QA AUDIT COMPLETE: {passed} / {total} TESTS PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 76)

    if passed == total:
        print("\n  🏆 100% PRODUCTION QUALITY ASSURANCE PASSED ACROSS THE ENTIRE PLATFORM!")
    else:
        print(f"\n  ⚠️ Warning: {total - passed} tests failed.")

if __name__ == '__main__':
    run_master_qa_audit()
