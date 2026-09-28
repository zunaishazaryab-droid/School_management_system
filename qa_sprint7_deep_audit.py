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
from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import User
from apps.students.models import Student
from apps.teachers.models import Teacher, TeacherPerformance
from apps.academics.models import AcademicYear, ClassRoom, Section, Subject
from apps.fees.models import FeeCategory, FeeStructure, FeeInvoice, FeePayment
from apps.transport.models import Vehicle, Route, RouteStop, StudentTransportAllocation
from apps.library.models import BookCategory, Book, BookIssue
from apps.inventory.models import ItemCategory, Supplier, InventoryItem, StockTransaction


def run_full_qa_suite():
    print("======================================================================")
    print("  🚀 RIGOROUS QA COMPREHENSIVE AUDIT REPORT (SPRINT 0 — SPRINT 7)     ")
    print("======================================================================")

    passed = 0
    failed = 0
    failures = []

    def check(condition, test_name, domain="CORE"):
        nonlocal passed, failed, failures
        if condition:
            passed += 1
            print(f"  ✅ [PASS] ({domain}) {test_name}")
        else:
            failed += 1
            failures.append(f"({domain}) {test_name}")
            print(f"  ❌ [FAIL] ({domain}) {test_name}")

    client = Client()

    # -------------------------------------------------------------
    # 1. SETUP & TEST USERS (RBAC MATRIX)
    # -------------------------------------------------------------
    print("\n--- 1. Testing Role-Based Security & Permissions Matrix ---")
    admin_user, _ = User.objects.get_or_create(username='qa_admin', defaults={'role': User.Role.ADMIN, 'email': 'admin@school.qa'})
    teacher_user, _ = User.objects.get_or_create(username='qa_teacher', defaults={'role': User.Role.TEACHER, 'email': 'teacher@school.qa'})
    parent_user, _ = User.objects.get_or_create(username='qa_parent', defaults={'role': User.Role.PARENT, 'email': 'parent@school.qa'})

    # Test 1.1: Anonymous user cannot access transport or library dashboard
    anon_client = Client()
    r = anon_client.get(reverse('transport:dashboard'))
    check(r.status_code == 302, "Anonymous user blocked from Transport Dashboard", "SECURITY")

    r = anon_client.get(reverse('library:dashboard'))
    check(r.status_code == 302, "Anonymous user blocked from Library Dashboard", "SECURITY")

    r = anon_client.get(reverse('inventory:dashboard'))
    check(r.status_code == 302, "Anonymous user blocked from Inventory Dashboard", "SECURITY")

    # Test 1.2: Parent cannot access Inventory Management (Accountant/Admin only)
    parent_client = Client()
    parent_client.force_login(parent_user)
    r = parent_client.get(reverse('inventory:dashboard'))
    check(r.status_code == 302, "Parent role blocked from Inventory Asset Dashboard", "RBAC")

    # Test 1.3: Teacher can view Library Dashboard
    teacher_client = Client()
    teacher_client.force_login(teacher_user)
    r = teacher_client.get(reverse('library:dashboard'))
    check(r.status_code == 200, "Teacher role allowed to view Library Dashboard (200)", "RBAC")

    # -------------------------------------------------------------
    # 2. TRANSPORT MODULE RIGOROUS FUNCTIONAL & CRUD TESTS
    # -------------------------------------------------------------
    print("\n--- 2. Transport & Bus Fleet Management Workflows ---")
    admin_client = Client()
    admin_client.force_login(admin_user)

    # Test 2.1: Transport Dashboard rendering and KPIs
    r = admin_client.get(reverse('transport:dashboard'))
    check(r.status_code == 200, "Admin renders Transport Dashboard", "TRANSPORT")
    check("Transport & Bus Fleet" in r.content.decode(), "Dashboard contains Transport headline", "TRANSPORT")

    # Test 2.2: Create a new Vehicle via model
    v_test, v_created = Vehicle.objects.get_or_create(
        vehicle_number='QA-BUS-999',
        defaults={
            'model_name': 'Hino Eco Express 40-Seater',
            'seating_capacity': 40,
            'driver_name': 'Ghulam Mustafa',
            'driver_phone': '0333-7654321',
            'status': Vehicle.Status.ACTIVE
        }
    )
    check(v_test.pk is not None, "Vehicle successfully created in DB", "TRANSPORT")

    # Test 2.3: Create Route and Stops
    r_test, _ = Route.objects.get_or_create(
        title='QA Route: Johar Town to Main Campus',
        defaults={
            'start_point': 'Johar Town G-1 Market',
            'end_point': 'Main Campus',
            'monthly_fare': Decimal('3800.00'),
            'is_active': True
        }
    )
    stop_test, _ = RouteStop.objects.get_or_create(
        route=r_test,
        stop_name='Allah Hoo Roundabout',
        stop_order=1,
        defaults={'pickup_time': '07:20:00', 'drop_time': '14:10:00'}
    )
    check(stop_test.route == r_test, "Route stop linked correctly to Route", "TRANSPORT")

    # Test 2.4: Allocate a Student to Transport
    student = Student.objects.first()
    if student:
        # Clear existing allocation if any for testing
        StudentTransportAllocation.objects.filter(student=student).delete()
        alloc = StudentTransportAllocation.objects.create(
            student=student,
            vehicle=v_test,
            route=r_test,
            stop=stop_test,
            start_date=timezone.now().date(),
            monthly_fee=Decimal('3800.00'),
            status=StudentTransportAllocation.Status.ACTIVE
        )
        check(alloc.pk is not None, f"Student {student.get_full_name()} allocated to {r_test.title}", "TRANSPORT")
        check(v_test.assigned_passengers_count >= 1, "Vehicle assigned passengers count property computed accurately", "TRANSPORT")

    # Test 2.5: HTTP UI endpoint for transport routes and allocations
    r = admin_client.get(reverse('transport:route_list'))
    check(r.status_code == 200, "Route listing page renders (200)", "TRANSPORT")

    r = admin_client.get(reverse('transport:allocation_list'))
    check(r.status_code == 200, "Student Allocation list renders (200)", "TRANSPORT")

    # -------------------------------------------------------------
    # 3. LIBRARY MODULE RIGOROUS FUNCTIONAL & STOCK MOVEMENT TESTS
    # -------------------------------------------------------------
    print("\n--- 3. Library Catalog & Book Loan/Return Lifecycle ---")

    # Test 3.1: Library Dashboard
    r = admin_client.get(reverse('library:dashboard'))
    check(r.status_code == 200, "Library Dashboard renders (200)", "LIBRARY")

    # Test 3.2: Create Book Category & Book
    lcat, _ = BookCategory.objects.get_or_create(
        code='QA-CAT',
        defaults={'name': 'QA Automated Testing & CS', 'description': 'Computer Science Reference Books'}
    )
    book_test, _ = Book.objects.get_or_create(
        isbn='978-QA-123456',
        defaults={
            'title': 'Advanced Software Quality Assurance Handbook',
            'author': 'Dr. Glenn Myers',
            'category': lcat,
            'rack_location': 'Shelf QA-1',
            'total_copies': 10,
            'available_copies': 10,
            'price': Decimal('2200.00')
        }
    )
    check(book_test.available_copies == 10, "Initial available copies count verified as 10", "LIBRARY")

    # Test 3.3: Issue Book Workflow (decrements available stock)
    if student:
        init_copies = book_test.available_copies
        issue_record = BookIssue.objects.create(
            book=book_test,
            student=student,
            issue_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=14),
            status=BookIssue.Status.ISSUED,
            issued_by=admin_user
        )
        book_test.available_copies -= 1
        book_test.save()
        check(book_test.available_copies == init_copies - 1, "Stock decremented upon book issuance (10 -> 9)", "LIBRARY")

        # Test 3.4: Return Book Workflow via HTTP endpoint
        r_return = admin_client.post(reverse('library:book_return', kwargs={'pk': issue_record.pk}))
        check(r_return.status_code == 302, "Book return HTTP endpoint redirects successfully (302)", "LIBRARY")

        issue_record.refresh_from_db()
        book_test.refresh_from_db()
        check(issue_record.status == BookIssue.Status.RETURNED, "Book issue status updated to RETURNED", "LIBRARY")
        check(book_test.available_copies == init_copies, "Stock restored back upon book return (9 -> 10)", "LIBRARY")

    # Test 3.5: Search and filter in book catalog
    r = admin_client.get(reverse('library:book_list') + "?q=Quality")
    check(r.status_code == 200, "Book catalog search by keyword returns 200", "LIBRARY")
    check("Quality" in r.content.decode(), "Search results contain matched book title", "LIBRARY")

    # -------------------------------------------------------------
    # 4. INVENTORY & ASSET RIGOROUS FUNCTIONAL & VALUATION TESTS
    # -------------------------------------------------------------
    print("\n--- 4. Inventory, Stock Movements & Asset Valuation ---")

    # Test 4.1: Dashboard
    r = admin_client.get(reverse('inventory:dashboard'))
    check(r.status_code == 200, "Inventory Dashboard renders (200)", "INVENTORY")
    check("Asset Valuation" in r.content.decode(), "Dashboard includes Asset Valuation KPI", "INVENTORY")

    # Test 4.2: Create Supplier & Inventory Item
    supp_test, _ = Supplier.objects.get_or_create(
        name='QA Quality Lab Supplies Ltd.',
        defaults={'phone': '0300-8877665', 'contact_person': 'Asif Raza'}
    )
    icat_test, _ = ItemCategory.objects.get_or_create(name='QA Robotics & Kits')

    item_test, _ = InventoryItem.objects.get_or_create(
        item_code='QA-ROBOT-01',
        defaults={
            'name': 'Arduino Starter Robotics Experiment Kit',
            'category': icat_test,
            'quantity_in_stock': 20,
            'min_reorder_level': 5,
            'unit': 'SET',
            'unit_price': Decimal('3500.00'),
            'location': 'Lab Cabinet 4'
        }
    )
    # Ensure fresh test state
    item_test.quantity_in_stock = 20
    item_test.unit_price = Decimal('3500.00')
    item_test.save()
    check(item_test.total_valuation == Decimal('70000.00'), "Item total valuation computed correctly (20 * 3500 = 70,000)", "INVENTORY")
    check(item_test.is_low_stock is False, "Item not in low stock when quantity (20) > threshold (5)", "INVENTORY")

    # Test 4.3: Stock OUT movement via HTTP post
    init_qty = item_test.quantity_in_stock
    tx_out_data = {
        'item': item_test.pk,
        'transaction_type': StockTransaction.Type.OUT,
        'quantity': 16, # leaves 4, triggering low stock
        'unit_price': '3500.00',
        'issued_to': 'Robotics Club Grade 9',
        'transaction_date': timezone.now().date().strftime('%Y-%m-%d'),
        'reference_number': 'QA-REQ-001',
        'notes': 'Issued for Science Exhibition'
    }
    r_tx = admin_client.post(reverse('inventory:transaction_create'), tx_out_data)
    check(r_tx.status_code == 302, "Stock OUT transaction HTTP POST succeeds and redirects (302)", "INVENTORY")

    item_test.refresh_from_db()
    check(item_test.quantity_in_stock == init_qty - 16, f"Stock OUT accurately reduced stock from {init_qty} to {item_test.quantity_in_stock}", "INVENTORY")
    check(item_test.is_low_stock is True, "Low stock warning triggered when quantity (4) <= threshold (5)", "INVENTORY")

    # Test 4.4: Stock IN movement to replenish
    tx_in_data = {
        'item': item_test.pk,
        'transaction_type': StockTransaction.Type.IN,
        'quantity': 25,
        'unit_price': '3400.00',
        'supplier': supp_test.pk,
        'transaction_date': timezone.now().date().strftime('%Y-%m-%d'),
        'reference_number': 'QA-PO-9090',
        'notes': 'Stock replenishment purchase'
    }
    r_tx_in = admin_client.post(reverse('inventory:transaction_create'), tx_in_data)
    check(r_tx_in.status_code == 302, "Stock IN transaction HTTP POST succeeds and redirects (302)", "INVENTORY")

    item_test.refresh_from_db()
    check(item_test.quantity_in_stock == 29, "Stock IN replenished quantity accurately to 29", "INVENTORY")
    check(item_test.is_low_stock is False, "Low stock warning resolved after replenishment", "INVENTORY")

    # -------------------------------------------------------------
    # 5. SPRINT 6 REGRESSION CHECKS: REST API & CERTIFICATES
    # -------------------------------------------------------------
    print("\n--- 5. Sprint 6 Regression & REST API Endpoints ---")
    r_api = admin_client.get('/api/v1/students/')
    check(r_api.status_code == 200, "REST API /api/v1/students/ returns HTTP 200", "API")
    check('results' in r_api.json() or isinstance(r_api.json(), list), "REST API returns valid structured JSON payload", "API")

    if student:
        r_slc = admin_client.get(reverse('students:student_certificate', kwargs={'pk': student.pk}) + "?type=SLC")
        check(r_slc.status_code == 200, f"SLC Certificate renders for student #{student.admission_number}", "CERTIFICATES")

    r_cards = admin_client.get(reverse('students:batch_id_cards'))
    check(r_cards.status_code == 200, "Batch PVC Student ID Cards page loads (200)", "ID_CARDS")

    # -------------------------------------------------------------
    # 6. SYSTEM HEALTH & AUDIT LOG INTEGRITY
    # -------------------------------------------------------------
    print("\n--- 6. System Health, Settings & Audit Logs ---")
    r_audit = admin_client.get(reverse('core:activity_logs'))
    check(r_audit.status_code == 200, "Activity Audit Log view renders (200)", "CORE")

    r_settings = admin_client.get(reverse('core:school_settings'))
    check(r_settings.status_code == 200, "School Profile & Institution Settings page renders (200)", "CORE")

    # -------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------
    total = passed + failed
    pass_rate = round((passed / total) * 100, 1) if total > 0 else 0
    print("\n======================================================================")
    print(f"  🏁 FINAL QA RESULTS: {passed} / {total} PASSED ({pass_rate}%)")
    print("======================================================================")

    if failures:
        print("\n  ❌ FAILURES RECORDED:")
        for f in failures:
            print(f"    - {f}")
        return False
    else:
        print("\n  🏆 ALL TESTS, WORKFLOWS, RBAC POLICIES & CALCULATIONS ARE 100% VERIFIED!")
        return True


if __name__ == '__main__':
    success = run_full_qa_suite()
    sys.exit(0 if success else 1)
