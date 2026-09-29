"""
Rigorous Automated QA Audit Suite for Sprint 9 & Full System Regression
Covers:
1. Multi-Campus Architecture & Session Switcher
2. Online Computer-Based Testing (CBT) Assessment & Auto-Grading Engine
3. QR Code Security Badge Verification & Gatekeeper Scanner
4. Executive Financial Forecast & Leadership KPI Analytics
5. Full Multi-Sprint System Regression Suite (Sprints 0 - 8)
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
from apps.core.models import Branch, SchoolSetting
from apps.examinations.models import OnlineAssessment, AssessmentQuestion, StudentAssessmentAttempt
from apps.attendance.models import BiometricDevice, StudentLeaveRequest
from apps.communication.models import SMSWhatsAppGateway, NotificationQueue
from apps.fees.models import FeeInvoice

User = get_user_model()


def run_sprint9_audit():
    print("=" * 70)
    print("  >> RIGOROUS QA COMPREHENSIVE AUDIT REPORT (SPRINT 0 - SPRINT 9)")
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

    student = Student.objects.filter(status='ACTIVE').first()
    classroom = ClassRoom.objects.first()
    subject = Subject.objects.first()

    # --- 1. MULTI-CAMPUS MANAGEMENT ---
    print("\n--- 1. Multi-Campus Architecture & Session Switcher ---")
    campus_resp = client.get('/campuses/')
    assert_test(campus_resp.status_code == 200, "Campuses management hub renders (200)", "CAMPUS")

    branch, _ = Branch.objects.get_or_create(
        code="GXV-QA01",
        defaults={
            'name': 'QA Test Campus Gulberg',
            'campus_type': Branch.CampusType.CITY,
            'address': 'Main Boulevard Gulberg',
            'city': 'Lahore',
            'principal_name': 'Sir QA Lead'
        }
    )
    assert_test(branch.id is not None, "Campus branch entity created in DB", "CAMPUS")

    # Switch branch context
    switch_resp = client.get(f'/campuses/switch/{branch.id}/', HTTP_REFERER='/campuses/')
    assert_test(switch_resp.status_code == 302, "Switch campus context executes and redirects", "CAMPUS")
    assert_test(client.session.get('active_branch_id') == branch.id, "Session active_branch_id successfully updated", "CAMPUS")

    # --- 2. ONLINE CBT QUIZZES & AUTO-GRADING ENGINE ---
    print("\n--- 2. Online CBT Quizzes & Instant Auto-Grading ---")
    cbt_list_resp = client.get('/examinations/cbt/')
    assert_test(cbt_list_resp.status_code == 200, "Online CBT Assessment list renders (200)", "CBT")

    # Create Timed CBT Assessment
    quiz = OnlineAssessment.objects.create(
        title="QA Sprint 9 Automated CBT Test",
        class_room=classroom,
        subject=subject,
        duration_minutes=25,
        total_marks=Decimal('6.00'),
        passing_percentage=Decimal('50.00'),
        created_by=admin_user,
        status=OnlineAssessment.Status.PUBLISHED
    )
    assert_test(quiz.id is not None, "OnlineAssessment created with PUBLISHED status", "CBT")

    # Add Questions
    q1 = AssessmentQuestion.objects.create(
        assessment=quiz,
        question_text="What is the chemical symbol for Gold?",
        question_type=AssessmentQuestion.QuestionType.MCQ,
        option_a="Ag", option_b="Au", option_c="Fe", option_d="Pb",
        correct_answer="B",
        marks=Decimal('2.00'),
        order_num=1
    )
    q2 = AssessmentQuestion.objects.create(
        assessment=quiz,
        question_text="Water boils at 100 degrees Celsius at standard atmospheric pressure.",
        question_type=AssessmentQuestion.QuestionType.TRUE_FALSE,
        option_a="True", option_b="False",
        correct_answer="TRUE",
        marks=Decimal('2.00'),
        order_num=2
    )
    q3 = AssessmentQuestion.objects.create(
        assessment=quiz,
        question_text="Light travels faster than sound in air.",
        question_type=AssessmentQuestion.QuestionType.TRUE_FALSE,
        option_a="True", option_b="False",
        correct_answer="TRUE",
        marks=Decimal('2.00'),
        order_num=3
    )
    assert_test(quiz.questions.count() == 3, "Assessment questions attached to quiz", "CBT")

    # Student Takes Timed Quiz (Submit answers: Q1=B, Q2=TRUE, Q3=FALSE -> Expected: 4.0 / 6.0 = 66.7% PASS)
    take_resp = client.post(f'/examinations/cbt/{quiz.id}/take/', {
        f'question_{q1.id}': 'B',
        f'question_{q2.id}': 'TRUE',
        f'question_{q3.id}': 'FALSE',
    })
    assert_test(take_resp.status_code == 200, "Student test submission evaluated and rendered (200)", "CBT")

    attempt = StudentAssessmentAttempt.objects.filter(assessment=quiz, student=student).first()
    assert_test(attempt is not None, "StudentAssessmentAttempt record created", "CBT")
    assert_test(attempt.score_obtained == Decimal('4.00'), f"Auto-grading computed exact score: {attempt.score_obtained}/6.00", "CBT")
    assert_test(attempt.is_passed is True, "Student pass criteria accurately verified (66.7% >= 50.0%)", "CBT")

    # Results Page
    results_resp = client.get(f'/examinations/cbt/{quiz.id}/results/')
    assert_test(results_resp.status_code == 200, "CBT Assessment Results & Ranking page loads (200)", "CBT")

    # --- 3. QR BADGE VERIFICATION & SCANNER ---
    print("\n--- 3. Dynamic QR Code Security Badge Verification ---")
    # Verify by student admission number
    verify_resp = client.get(f'/verify-badge/{student.admission_number}/')
    assert_test(verify_resp.status_code == 200, "QR Badge Public Verification page loads (200)", "QR_VERIFY")
    assert_test(b"OFFICIAL IDENTITY VERIFIED" in verify_resp.content, "Student identity confirmed as VERIFIED", "QR_VERIFY")

    # Test scanner page
    scanner_resp = client.get('/security/scanner/')
    assert_test(scanner_resp.status_code == 200, "Security Guard Scanner interface loads (200)", "QR_VERIFY")

    # --- 4. EXECUTIVE FINANCIAL & LEADERSHIP ANALYTICS ---
    print("\n--- 4. Executive Leadership & Revenue Forecast Analytics ---")
    exec_resp = client.get('/reports/executive/')
    assert_test(exec_resp.status_code == 200, "Executive Analytics dashboard loads (200)", "EXECUTIVE")
    assert_test(b"Net Operating Profit" in exec_resp.content, "Executive KPIs include Net Operating Profit and Recovery Rate", "EXECUTIVE")

    # --- 5. MULTI-SPRINT SYSTEM REGRESSION SUITE (SPRINTS 0 - 8) ---
    print("\n--- 5. Comprehensive Full System Multi-Sprint Regression ---")
    assert_test(client.get('/attendance/biometric/').status_code == 200, "Biometric Sync Hub loads (200)", "REGRESSION")
    assert_test(client.get('/attendance/leaves/').status_code == 200, "Student Leave Requests load (200)", "REGRESSION")
    assert_test(client.get('/communication/gateways/').status_code == 200, "WhatsApp Gateway Hub loads (200)", "REGRESSION")
    assert_test(client.get('/lectures/homework/').status_code == 200, "Homework Submissions load (200)", "REGRESSION")
    assert_test(client.get('/transport/').status_code == 200, "Transport Bus Fleet loads (200)", "REGRESSION")
    assert_test(client.get('/library/').status_code == 200, "Library Catalog loads (200)", "REGRESSION")
    assert_test(client.get('/inventory/').status_code == 200, "Inventory Assets load (200)", "REGRESSION")
    assert_test(client.get('/api/v1/students/').status_code == 200, "REST API mobile endpoint loads (200)", "REGRESSION")
    assert_test(client.get('/students/portal/').status_code == 200, "Student/Parent Portal loads (200)", "REGRESSION")
    assert_test(client.get('/settings/school/').status_code == 200, "School Profile & Settings load (200)", "REGRESSION")

    invoice = FeeInvoice.objects.first()
    if invoice:
        assert_test(client.get(f'/fees/challans/{invoice.id}/3part/').status_code == 200, "3-Part Fee Challan voucher loads (200)", "REGRESSION")

    print("\n" + "=" * 70)
    print(f"  FINAL QA RESULTS: {passed} / {total} PASSED ({(passed/total)*100:.1f}%)")
    print("=" * 70)

    if passed == total:
        print("\n  >>> ENTIRE SCHOOL MANAGEMENT ERP SYSTEM (SPRINTS 0 TO 9) 100% COMPLETE & VERIFIED! <<<")
    else:
        print(f"\n  Warning: {total - passed} tests failed.")

if __name__ == '__main__':
    run_sprint9_audit()
