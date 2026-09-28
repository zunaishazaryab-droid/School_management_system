import os
import sys
import io
import django

# Force UTF-8 on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from apps.accounts.models import User
from apps.students.models import Student
from apps.teachers.models import Teacher, TeacherPerformance
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject, Period, TimetableEntry
from apps.attendance.models import StudentAttendance, TeacherAttendance
from apps.lectures.models import DailyLecture, Homework
from apps.syllabus.models import SyllabusChapter, SyllabusTopic
from apps.fees.models import FeeCategory, FeeStructure, FeeInvoice, FeePayment
from apps.examinations.models import Exam, ExamSchedule, ExamMarks, ExamStudentResult
from apps.expenses.models import ExpenseCategory, Expense
from apps.communication.models import Announcement, MessageTemplate, DirectMessageLog
from apps.core.models import SchoolSetting, Notification, ActivityLog

def run_qa_audit():
    print("======================================================================")
    print("       🎓 SCHOOL MANAGEMENT SYSTEM — FULL QA AUDIT & TEST SUITE       ")
    print("======================================================================")
    
    passed_tests = 0
    total_tests = 0
    failures = []

    def assert_test(condition, test_name, domain="CORE"):
        nonlocal passed_tests, total_tests, failures
        total_tests += 1
        if condition:
            passed_tests += 1
            print(f"  [PASS] ({domain}) {test_name}")
        else:
            failures.append(f"({domain}) {test_name}")
            print(f"  [FAIL] ({domain}) {test_name}")

    client = Client()

    # ---------------------------------------------------------
    # 1. AUTHENTICATION & ROLE-BASED ACCESS CONTROL (RBAC)
    # ---------------------------------------------------------
    print("\n--- 1. Testing Authentication, Roles & RBAC ---")
    
    # Check Admin login
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        admin_user = User.objects.create_superuser('admin_qa', 'admin@qa.com', 'adminpass', role='ADMIN')
    
    client.force_login(admin_user)
    resp = client.get(reverse('core:dashboard'))
    assert_test(resp.status_code == 200, "Admin Dashboard renders (Status 200)", "AUTH")
    assert_test("Dashboard" in resp.content.decode(), "Admin Dashboard contains title", "AUTH")

    # Check anonymous redirection
    anon_client = Client()
    resp_anon = anon_client.get(reverse('core:dashboard'))
    assert_test(resp_anon.status_code == 302, "Anonymous user redirected to login", "AUTH")

    # ---------------------------------------------------------
    # 2. ACADEMICS & STUDENTS MODULE
    # ---------------------------------------------------------
    print("\n--- 2. Testing Academics & Students Module ---")
    resp = client.get(reverse('students:student_list'))
    assert_test(resp.status_code == 200, "Student directory page loads (200)", "STUDENTS")

    student = Student.objects.first()
    if student:
        resp = client.get(reverse('students:student_detail', kwargs={'pk': student.pk}))
        assert_test(resp.status_code == 200, f"Student profile loads for {student.get_full_name()} (200)", "STUDENTS")
        assert_test("Overview" in resp.content.decode() or "Academic" in resp.content.decode(), "Student multi-tab profile tabs present", "STUDENTS")

    resp = client.get(reverse('academics:class_list'))
    assert_test(resp.status_code == 200, "Classes & Sections list renders (200)", "ACADEMICS")

    resp = client.get(reverse('academics:timetable'))
    assert_test(resp.status_code == 200, "Timetable Matrix page renders (200)", "ACADEMICS")

    # ---------------------------------------------------------
    # 3. FACULTY & STAFF, PAYROLL & PERFORMANCE
    # ---------------------------------------------------------
    print("\n--- 3. Testing Faculty, Attendance & Performance ---")
    resp = client.get(reverse('teachers:teacher_list'))
    assert_test(resp.status_code == 200, "Faculty directory page loads (200)", "TEACHERS")

    teacher = Teacher.objects.first()
    if teacher:
        resp = client.get(reverse('teachers:teacher_detail', kwargs={'pk': teacher.pk}))
        assert_test(resp.status_code == 200, f"Faculty profile loads for {teacher.get_full_name()} (200)", "TEACHERS")

    resp = client.get(reverse('teachers:performance_dashboard'))
    assert_test(resp.status_code == 200, "Teacher Performance & Appraisal Hub renders (200)", "TEACHERS")

    perf = TeacherPerformance.objects.first()
    if perf:
        resp = client.get(reverse('teachers:performance_detail', kwargs={'pk': perf.pk}))
        assert_test(resp.status_code == 200, "Teacher Performance Scorecard sheet loads (200)", "TEACHERS")

    # ---------------------------------------------------------
    # 4. ATTENDANCE, LECTURES & SYLLABUS TRACKING
    # ---------------------------------------------------------
    print("\n--- 4. Testing Attendance, Daily Lectures & Syllabus ---")
    resp = client.get(reverse('attendance:student_attendance'))
    assert_test(resp.status_code == 200, "Daily Student Attendance register loads (200)", "ATTENDANCE")

    resp = client.get(reverse('lectures:lecture_list'))
    assert_test(resp.status_code == 200, "Daily Lectures & Homework Diary list loads (200)", "LECTURES")

    resp = client.get(reverse('syllabus:tracker'))
    assert_test(resp.status_code == 200, "Syllabus Completion Tracker page loads (200)", "SYLLABUS")

    # ---------------------------------------------------------
    # 5. FEE MANAGEMENT, CHALLANS & EXPENSES
    # ---------------------------------------------------------
    print("\n--- 5. Testing Fees, Invoices & Expenses ---")
    resp = client.get(reverse('fees:fee_dashboard'))
    assert_test(resp.status_code == 200, "Fee Management dashboard loads (200)", "FEES")

    invoice = FeeInvoice.objects.first()
    if invoice:
        resp = client.get(reverse('fees:invoice_detail', kwargs={'pk': invoice.pk}))
        assert_test(resp.status_code == 200, f"Printable 3-Copy Fee Challan loads for #{invoice.invoice_number} (200)", "FEES")

    resp = client.get(reverse('fees:defaulters_list'))
    assert_test(resp.status_code == 200, "Defaulters & Dues list renders (200)", "FEES")

    resp = client.get(reverse('expenses:expense_list'))
    assert_test(resp.status_code == 200, "Expenses management page loads (200)", "EXPENSES")

    # ---------------------------------------------------------
    # 6. EXAMINATIONS, RESULTS & REPORT CARDS
    # ---------------------------------------------------------
    print("\n--- 6. Testing Examinations, Marks & Report Cards ---")
    resp = client.get(reverse('examinations:exam_list'))
    assert_test(resp.status_code == 200, "Examinations hub loads (200)", "EXAMS")

    exam_res = ExamStudentResult.objects.first()
    if exam_res:
        resp = client.get(reverse('examinations:student_report_card', kwargs={'exam_id': exam_res.exam_id, 'student_id': exam_res.student_id}))
        assert_test(resp.status_code == 200, f"Official Printable Student Report Card loads for {exam_res.student.get_full_name()} (200)", "EXAMS")

    # ---------------------------------------------------------
    # 7. REPORTS CENTER & PDF/EXCEL EXPORTS
    # ---------------------------------------------------------
    print("\n--- 7. Testing Central Reports Hub ---")
    resp = client.get(reverse('reports:reports_hub'))
    assert_test(resp.status_code == 200, "Central Reports Center loads (200)", "REPORTS")

    resp = client.get(reverse('reports:student_report'))
    assert_test(resp.status_code == 200, "Student Filtered Report loads (200)", "REPORTS")

    # ---------------------------------------------------------
    # 8. COMMUNICATION, NOTICE BOARD & BROADCASTS (SPRINT 5)
    # ---------------------------------------------------------
    print("\n--- 8. Testing Sprint 5 Communication & Notice Board ---")
    resp = client.get(reverse('communication:announcement_list'))
    assert_test(resp.status_code == 200, "Notice Board / Announcements list renders (200)", "COMMUNICATION")

    ann = Announcement.objects.first()
    if ann:
        resp = client.get(reverse('communication:announcement_detail', kwargs={'pk': ann.pk}))
        assert_test(resp.status_code == 200, f"Printable Official Circular Sheet loads for '{ann.title}' (200)", "COMMUNICATION")

    resp = client.get(reverse('communication:broadcast_center'))
    assert_test(resp.status_code == 200, "Parent & Faculty Broadcast Center renders (200)", "COMMUNICATION")

    # Test dynamic WhatsApp message generation
    if student:
        post_data = {
            'send_direct': '1',
            'channel': 'WHATSAPP',
            'recipient_type': 'STUDENT',
            'student_id': str(student.id),
            'message_body': 'Dear {guardian_name}, fee for {student_name} is due.'
        }
        resp = client.post(reverse('communication:broadcast_center'), post_data)
        assert_test(resp.status_code == 200, "WhatsApp broadcast link dispatched and generated (200)", "COMMUNICATION")
        assert_test("wa.me" in resp.content.decode() or "Message Ready" in resp.content.decode(), "WhatsApp Web launcher link generated", "COMMUNICATION")

    resp = client.get(reverse('communication:template_list'))
    assert_test(resp.status_code == 200, "Message Templates page renders (200)", "COMMUNICATION")

    resp = client.get(reverse('communication:history'))
    assert_test(resp.status_code == 200, "Communication Dispatch History log renders (200)", "COMMUNICATION")

    # ---------------------------------------------------------
    # 9. SEARCH, NOTIFICATIONS, AUDIT LOG & SETTINGS (SPRINT 5)
    # ---------------------------------------------------------
    print("\n--- 9. Testing Sprint 5 Search, Notifications, Audit & Settings ---")
    
    # Test Global Search with student query
    search_q = student.first_name if student else "Ali"
    resp = client.get(reverse('core:global_search') + f"?q={search_q}")
    assert_test(resp.status_code == 200, f"Global search for '{search_q}' executed (200)", "CORE")
    assert_test("Students" in resp.content.decode(), "Global search found Categorized Student Results", "CORE")

    # Notifications
    resp = client.get(reverse('core:notifications'))
    assert_test(resp.status_code == 200, "Notifications page renders (200)", "CORE")

    # Activity Logs (Audit Trail)
    resp = client.get(reverse('core:activity_logs'))
    assert_test(resp.status_code == 200, "System Activity Log & Audit Trail renders (200)", "CORE")

    # School Settings
    resp = client.get(reverse('core:school_settings'))
    assert_test(resp.status_code == 200, "Institution Profile & Settings page renders (200)", "CORE")

    # Staff User Management
    resp = client.get(reverse('core:user_management'))
    assert_test(resp.status_code == 200, "Staff User Management page renders (200)", "CORE")

    # Database Backup Diagnostics & Download
    resp = client.get(reverse('core:database_backup'))
    assert_test(resp.status_code == 200, "Database Backup & Disaster Recovery page renders (200)", "CORE")

    resp_download = client.get(reverse('core:database_download') + "?format=sqlite")
    assert_test(resp_download.status_code == 200, "Database SQLite binary backup download stream works (200)", "CORE")
    assert_test("attachment" in resp_download.headers.get('Content-Disposition', ''), "Content-Disposition attachment header present", "CORE")

    # ---------------------------------------------------------
    # FINAL QA SUMMARY REPORT
    # ---------------------------------------------------------
    print("\n======================================================================")
    print(f"       QA AUDIT RESULTS: {passed_tests} / {total_tests} TESTS PASSED ({round(passed_tests/total_tests*100, 1)}%)")
    print("======================================================================")
    if failures:
        print("  FAILURES ENCOUNTERED:")
        for f in failures:
            print(f"   - {f}")
        return False
    else:
        print("  🎉 ALL MODULES, WORKFLOWS, RBAC POLICIES & ENDPOINTS PASSED QA AUDIT!")
        return True

if __name__ == '__main__':
    success = run_qa_audit()
    sys.exit(0 if success else 1)
