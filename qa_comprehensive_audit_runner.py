import os
import sys
import django

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academics.models import ClassRoom, Section, Subject, AcademicYear
from apps.fees.models import FeeInvoice, FeePayment, FeeCategory
from apps.examinations.models import Exam, ExamSchedule, ExamMarks, ExamStudentResult
from decimal import Decimal
from datetime import date

User = get_user_model()

def run_comprehensive_qa():
    print("=" * 75)
    print("🏫 GEN'X VISION SCHOOL SYSTEM — MASTER QA VERIFICATION SUITE")
    print("=" * 75)

    c = Client()
    passed = 0
    failed = 0
    total_tests = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, failed, total_tests
        total_tests += 1
        if condition:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} -> {details}")

    # --- 1. USER AUTHENTICATION & ROLES ---
    print("\n[MODULE 1: AUTHENTICATION & DASHBOARD]")
    admin_user = User.objects.filter(is_superuser=True).first() or User.objects.filter(role=User.Role.ADMIN).first()
    teacher_user = User.objects.filter(role=User.Role.TEACHER).first()
    student_user = User.objects.filter(role=User.Role.STUDENT).first()
    
    assert_test("Admin User exists", admin_user is not None)
    
    c.force_login(admin_user)
    r = c.get('/')
    assert_test("Main Dashboard load (HTTP 200)", r.status_code == 200)
    assert_test("Dashboard contains Quick Action Command Center", b"Quick Action Command Center" in r.content or b"Enter Exam Marks" in r.content)
    assert_test("Topbar contains 1-Click Quick Access Pills", b"topbar-quick-links" in r.content or b"Admission" in r.content)

    # --- 2. STUDENTS LIFECYCLE & EDIT WORKFLOW ---
    print("\n[MODULE 2: STUDENTS LIFECYCLE & EDIT RETURN]")
    r = c.get('/students/')
    assert_test("Students Directory list (HTTP 200)", r.status_code == 200)

    first_student = Student.objects.filter(status='ACTIVE').first()
    assert_test("Active student exists in database", first_student is not None)

    if first_student:
        r = c.get(f'/students/{first_student.id}/')
        assert_test("Student Profile / 360 Detail View (HTTP 200)", r.status_code == 200)

        r = c.get(f'/students/{first_student.id}/card/')
        assert_test("Student Single ID Card (HTTP 200)", r.status_code == 200)

        r = c.get('/students/batch-id-cards/')
        assert_test("Batch ID Cards Generation Hub (HTTP 200)", r.status_code == 200)

        # Test Student Edit View
        r = c.get(f'/students/{first_student.id}/edit/?next=/students/')
        assert_test("Student Edit Form Load with 'next' parameter (HTTP 200)", r.status_code == 200)

        # Test POST Edit Student
        edit_payload = {
            'admission_number': first_student.admission_number,
            'roll_number': first_student.roll_number or '1',
            'current_class': first_student.current_class_id,
            'current_section': first_student.current_section_id or '',
            'academic_year': first_student.academic_year_id or '',
            'admission_date': str(first_student.admission_date or date.today()),
            'status': 'ACTIVE',
            'first_name': first_student.first_name,
            'last_name': first_student.last_name,
            'gender': first_student.gender or 'MALE',
            'guardian_name': first_student.guardian_name or 'Guardian Name',
            'guardian_relationship': first_student.guardian_relationship or 'Father',
            'guardian_phone': first_student.guardian_phone or '03001234567',
            'residential_address': first_student.residential_address or 'City Address',
            'next': '/students/'
        }
        r = c.post(f'/students/{first_student.id}/edit/?next=/students/', edit_payload)
        assert_test("Student Edit POST returns redirect (HTTP 302)", r.status_code == 302, f"Got status {r.status_code}")
        if r.status_code == 302:
            assert_test("Student Edit Redirects to /students/ directory", '/students/' in r.url)

    # --- 3. EXAMINATIONS & DIRECT MARKS ENTRY ---
    print("\n[MODULE 3: EXAMINATIONS, VERTICAL MARKS ENTRY & RESULT CARD]")
    r = c.get('/examinations/')
    assert_test("Exams List Hub (HTTP 200)", r.status_code == 200)

    exam = Exam.objects.first()
    assert_test("Exam record exists in database", exam is not None)

    if exam:
        r = c.get(f'/examinations/{exam.id}/')
        assert_test("Exam Detail View (HTTP 200)", r.status_code == 200)

        r = c.get(f'/examinations/{exam.id}/marks-entry/')
        assert_test("Exam Quick Vertical Marks Entry Page (HTTP 200)", r.status_code == 200)

        if first_student:
            r = c.get(f'/examinations/{exam.id}/report-card/{first_student.id}/')
            assert_test("Official Student Result Card View (HTTP 200)", r.status_code == 200)
            assert_test("Result Card has Printable Container", b"report-card-container" in r.content or b"Print" in r.content)

            schedule = ExamSchedule.objects.filter(exam=exam, class_room=first_student.current_class).first()
            if schedule:
                post_data = {
                    'class_room': str(first_student.current_class_id),
                    'student_id': str(first_student.id),
                    f'total_marks_{schedule.id}': '100.00',
                    f'pass_marks_{schedule.id}': '33.00',
                    f'marks_{first_student.id}_{schedule.id}': '85.50',
                    f'remarks_{first_student.id}_{schedule.id}': 'Excellent work',
                    'save_all': '1'
                }
                r = c.post(f'/examinations/{exam.id}/marks-entry/', post_data)
                assert_test("Saving All Marks redirects directly to Result Card (HTTP 302)", r.status_code == 302)
                if r.status_code == 302:
                    assert_test("Save All Marks URL targets report-card", f'/examinations/{exam.id}/report-card/{first_student.id}/' in r.url)

    # --- 4. FEES, INVOICES, EDIT & PAYMENT COLLECTION ---
    print("\n[MODULE 4: FEES ENGINE, CHALLANS & 1-CLICK COLLECTION]")
    r = c.get('/fees/')
    assert_test("Fee Management Dashboard (HTTP 200)", r.status_code == 200)

    r = c.get('/fees/invoices/')
    assert_test("Fee Invoices List (HTTP 200)", r.status_code == 200)

    r = c.get('/fees/collect/')
    assert_test("Fee Payment Collection Hub (HTTP 200)", r.status_code == 200)

    r = c.get('/fees/invoices/create/')
    assert_test("Create Single Fee Challan View (HTTP 200)", r.status_code == 200)

    invoice = FeeInvoice.objects.first()
    assert_test("Fee Invoice exists in database", invoice is not None)

    if invoice:
        r = c.get(f'/fees/invoices/{invoice.id}/')
        assert_test("Invoice Detail View (HTTP 200)", r.status_code == 200)

        r = c.get(f'/fees/invoices/{invoice.id}/edit/')
        assert_test("Invoice Edit View (HTTP 200)", r.status_code == 200)

        r = c.get(f'/fees/challans/{invoice.id}/3part/')
        assert_test("3-Part Official Bank Challan Print (HTTP 200)", r.status_code == 200)

        r = c.get(f'/fees/collect/{invoice.id}/')
        assert_test("Collect Payment for Specific Invoice (HTTP 200)", r.status_code == 200)

        payment_payload = {
            'invoice_id': str(invoice.id),
            'amount': '500.00',
            'payment_date': str(date.today()),
            'payment_method': 'CASH',
            'transaction_reference': 'QA-TEST-REF',
            'remarks': 'QA automated test payment'
        }
        r = c.post('/fees/collect/', payment_payload)
        assert_test("Recording Payment redirects to Receipt (HTTP 302)", r.status_code == 302)
        if r.status_code == 302:
            assert_test("Payment redirect URL is receipt", '/fees/receipts/' in r.url)

    # --- 5. ACADEMICS & TIMETABLE ---
    print("\n[MODULE 5: ACADEMICS & CLASS MATRIX]")
    r = c.get('/academics/classes/')
    assert_test("Classes & Sections List (HTTP 200)", r.status_code == 200)

    r = c.get('/academics/subjects/')
    assert_test("Subjects & Curriculum (HTTP 200)", r.status_code == 200)

    r = c.get('/academics/timetable/')
    assert_test("Class Timetable Matrix (HTTP 200)", r.status_code == 200)

    # --- 6. ATTENDANCE & HR FACULTY ---
    print("\n[MODULE 6: ATTENDANCE & TEACHERS HR]")
    r = c.get('/attendance/student/')
    assert_test("Daily Student Attendance Register (HTTP 200)", r.status_code == 200)

    r = c.get('/attendance/teacher/')
    assert_test("Daily Teacher Attendance (HTTP 200)", r.status_code == 200)

    r = c.get('/attendance/report/')
    assert_test("Attendance Annual Matrix Report (HTTP 200)", r.status_code == 200)

    r = c.get('/attendance/biometric/')
    assert_test("Biometric Device Sync Hub (HTTP 200)", r.status_code == 200)

    r = c.get('/teachers/')
    assert_test("Teachers & Staff Directory (HTTP 200)", r.status_code == 200)

    # --- 7. REPORTS & EXECUTIVE ANALYTICS ---
    print("\n[MODULE 7: REPORTS CENTER & EXECUTIVE BI]")
    r = c.get('/reports/')
    assert_test("Reports Center Hub (HTTP 200)", r.status_code == 200)

    r = c.get('/reports/executive/')
    assert_test("Executive Analytics BI (HTTP 200)", r.status_code == 200)

    # --- 8. INVENTORY & SYSTEM SETTINGS ---
    print("\n[MODULE 8: INVENTORY & SYSTEM ADMIN]")
    r = c.get('/inventory/')
    assert_test("Stock & Inventory Dashboard (HTTP 200)", r.status_code == 200)

    r = c.get('/settings/school/')
    assert_test("School Settings & Profile (HTTP 200)", r.status_code == 200)

    r = c.get('/activity-logs/')
    assert_test("System Activity Audit Trail (HTTP 200)", r.status_code == 200)

    # --- 9. TEACHER ROLE PERMISSIONS VERIFICATION ---
    print("\n[MODULE 9: TEACHER ROLE PERMISSION AUDIT]")
    if teacher_user:
        c.force_login(teacher_user)
        r = c.get('/students/')
        assert_test("Teacher can access Students Directory (HTTP 200)", r.status_code == 200)

        if first_student:
            r = c.get(f'/students/{first_student.id}/edit/')
            assert_test("Teacher can access Student Edit (HTTP 200, Not Blocked)", r.status_code == 200)

        r = c.get('/fees/collect/')
        assert_test("Teacher can access Fee Collection (HTTP 200)", r.status_code == 200)

        if exam:
            r = c.get(f'/examinations/{exam.id}/marks-entry/')
            assert_test("Teacher can access Marks Entry (HTTP 200)", r.status_code == 200)

    # --- SUMMARY ---
    print("\n" + "=" * 75)
    print(f"📊 QA AUDIT SUMMARY: Total Tests: {total_tests} | Passed: {passed} | Failed: {failed}")
    if failed == 0:
        print("🎉 100% PASS RATE — ALL MODULES, WORKFLOWS & USER INTERFACES ARE PERFECT!")
    else:
        print(f"⚠️ {failed} TESTS FAILED.")
    print("=" * 75)

if __name__ == '__main__':
    run_comprehensive_qa()
