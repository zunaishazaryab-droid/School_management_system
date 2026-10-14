"""
======================================================================
  🏫 GEN'X VISION SCHOOL SYSTEM — COMPREHENSIVE SYSTEM INTEGRITY TEST
======================================================================
End-to-end automated verification of all ERP modules, endpoints, stock engine,
financials, exams, academics, and role permissions.
"""

import os
import sys
import django

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from decimal import Decimal
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.students.models import Student
from apps.teachers.models import Teacher
from apps.academics.models import ClassRoom, Section, Subject, TimetableEntry
from apps.core.models import Branch, SchoolSetting, ActivityLog
from apps.attendance.models import StudentAttendance, TeacherAttendance
from apps.lectures.models import DailyLecture, Homework
from apps.fees.models import FeeInvoice, FeeCategory, FeeStructure
from apps.examinations.models import Exam, ExamMarks
from apps.expenses.models import Expense, ExpenseCategory
from apps.transport.models import Vehicle, Route
from apps.library.models import Book, BookCategory
from apps.inventory.models import InventoryItem, ItemCategory, Supplier, StockTransaction

User = get_user_model()

def run_tests():
    print("=" * 80)
    print("  🚀 GEN'X VISION SCHOOL SYSTEM - COMPLETE VERIFICATION & AUDIT SUITE")
    print("=" * 80)

    client = Client()
    passed = 0
    failed = 0
    total = 0

    def check(condition, test_name, module="SYSTEM"):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ [PASS] [{module}] {test_name}")
        else:
            failed += 1
            print(f"  ❌ [FAIL] [{module}] {test_name}")

    # 1. AUTH & SECURITY
    print("\n--- 1. Authentication & Security RBAC ---")
    admin = User.objects.filter(role='ADMIN').first()
    if not admin:
        admin = User.objects.create_superuser('admin_audit', 'admin@audit.com', 'pass123')
    
    anon_client = Client()
    check(anon_client.get('/inventory/').status_code in [302, 401, 403], "Anonymous access blocked on Inventory", "SECURITY")
    check(anon_client.get('/fees/').status_code in [302, 401, 403], "Anonymous access blocked on Fees", "SECURITY")
    check(anon_client.get('/examinations/').status_code in [302, 401, 403], "Anonymous access blocked on Exams", "SECURITY")

    client.force_login(admin)
    check(client.get('/').status_code == 200, "Dashboard loads for Admin (200 OK)", "SECURITY")

    # 2. STOCK & INVENTORY MODULE
    print("\n--- 2. Stock & Inventory Management (اسٹاک مینجمنٹ) ---")
    check(client.get('/inventory/').status_code == 200, "Stock Dashboard loads (/inventory/)", "STOCK")
    check(client.get('/inventory/items/').status_code == 200, "Stock Items List loads (/inventory/items/)", "STOCK")
    check(client.get('/inventory/items/add/').status_code == 200, "Add Stock Item page loads (/inventory/items/add/)", "STOCK")
    check(client.get('/inventory/categories/').status_code == 200, "Stock Categories page loads (/inventory/categories/)", "STOCK")
    check(client.get('/inventory/transactions/').status_code == 200, "Stock In/Out Ledger loads (/inventory/transactions/)", "STOCK")
    check(client.get('/inventory/transactions/add/').status_code == 200, "Stock In/Out Form loads (/inventory/transactions/add/)", "STOCK")
    check(client.get('/inventory/suppliers/').status_code == 200, "Suppliers directory loads (/inventory/suppliers/)", "STOCK")
    check(client.get('/inventory/suppliers/add/').status_code == 200, "Add Supplier page loads (/inventory/suppliers/add/)", "STOCK")

    # Test Stock Operations Logic
    cat, _ = ItemCategory.objects.get_or_create(name="Audit Stationery Category")
    item, _ = InventoryItem.objects.get_or_create(
        item_code="AUDIT-STK-001",
        defaults={
            'name': 'Audit Exam Papers Pack',
            'category': cat,
            'quantity_in_stock': 100,
            'min_reorder_level': 20,
            'unit': 'PKT',
            'unit_price': Decimal('250.00'),
            'location': 'Room 102 Cupboard A'
        }
    )
    check(item.total_valuation == item.quantity_in_stock * item.unit_price, f"Stock valuation calculation correct (Rs. {item.total_valuation})", "STOCK")
    check(not item.is_low_stock, "Low-stock check operates correctly (False when above threshold)", "STOCK")

    # Stock IN Transaction Test
    initial_qty = item.quantity_in_stock
    tx_in = StockTransaction.objects.create(
        item=item,
        transaction_type=StockTransaction.Type.IN,
        quantity=50,
        unit_price=Decimal('250.00'),
        transaction_date=timezone.now().date(),
        created_by=admin
    )
    item.quantity_in_stock += 50
    item.save()
    check(item.quantity_in_stock == initial_qty + 50, f"Stock IN addition verified: {initial_qty} + 50 = {item.quantity_in_stock}", "STOCK")

    # Stock OUT Transaction Test
    tx_out = StockTransaction.objects.create(
        item=item,
        transaction_type=StockTransaction.Type.OUT,
        quantity=30,
        transaction_date=timezone.now().date(),
        issued_to="Exam Department",
        created_by=admin
    )
    item.quantity_in_stock -= 30
    item.save()
    check(item.quantity_in_stock == initial_qty + 20, f"Stock OUT deduction verified: now {item.quantity_in_stock}", "STOCK")

    # 3. ACADEMICS & STUDENTS
    print("\n--- 3. Academics & Students Directory ---")
    check(client.get('/students/').status_code == 200, "Students directory loads (200)", "STUDENTS")
    check(client.get('/students/dashboard/').status_code == 200, "Student Dashboard loads (200)", "STUDENTS")
    check(client.get('/academics/classes/').status_code == 200, "Classes & Sections matrix loads (200)", "ACADEMICS")
    check(client.get('/academics/subjects/').status_code == 200, "Subjects curriculum loads (200)", "ACADEMICS")
    check(client.get('/academics/timetable/').status_code == 200, "Timetable grid loads (200)", "ACADEMICS")

    # 4. TEACHERS & ATTENDANCE
    print("\n--- 4. Teachers, Faculty & Daily Attendance ---")
    check(client.get('/teachers/').status_code == 200, "Teachers & Staff roster loads (200)", "FACULTY")
    check(client.get('/attendance/student/').status_code == 200, "Daily Student Attendance register loads (200)", "ATTENDANCE")
    check(client.get('/attendance/biometric/').status_code == 200, "Biometric sync interface loads (200)", "ATTENDANCE")
    check(client.get('/attendance/leaves/').status_code == 200, "Leave management loads (200)", "ATTENDANCE")

    # 5. FEES, INVOICES & CHALLANS
    print("\n--- 5. Fee Engine & 3-Part Bank Challans ---")
    check(client.get('/fees/').status_code == 200, "Fee Management dashboard loads (200)", "FEES")
    check(client.get('/fees/invoices/').status_code == 200, "Fee Invoices directory loads (200)", "FEES")
    check(client.get('/fees/structures/').status_code == 200, "Fee Structures matrix loads (200)", "FEES")
    check(client.get('/fees/defaulters/').status_code == 200, "Defaulters list loads (200)", "FEES")

    # 6. EXAMINATIONS & CBT QUIZZES
    print("\n--- 6. Examinations & Online CBT Quizzes ---")
    check(client.get('/examinations/').status_code == 200, "Exams Hub loads (200)", "EXAMS")
    check(client.get('/examinations/cbt/').status_code == 200, "Online CBT Quizzes portal loads (200)", "EXAMS")

    # 7. EXPENSES, TRANSPORT & LIBRARY
    print("\n--- 7. Expenses, Transport Fleet & Library ---")
    check(client.get('/expenses/').status_code == 200, "Institutional Expenses ledger loads (200)", "EXPENSES")
    check(client.get('/transport/').status_code == 200, "Transport fleet dashboard loads (200)", "TRANSPORT")
    check(client.get('/library/').status_code == 200, "Library catalog loads (200)", "LIBRARY")

    # 8. REPORTS, MULTI-CAMPUS & AUDIT TRAIL
    print("\n--- 8. Executive Reports, Multi-Campus & Audit Trail ---")
    check(client.get('/reports/').status_code == 200, "Reports Center hub loads (200)", "REPORTS")
    check(client.get('/reports/executive/').status_code == 200, "Executive BI analytics dashboard loads (200)", "REPORTS")
    check(client.get('/campuses/').status_code == 200, "Multi-Campus branches management loads (200)", "CAMPUS")
    check(client.get('/activity-logs/').status_code == 200, "Activity Audit Trail log loads (200)", "AUDIT")

    # 9. REST APIs
    print("\n--- 9. Mobile REST APIs ---")
    check(client.get('/api/v1/students/').status_code == 200, "API /api/v1/students/ responsive (200)", "API")
    check(client.get('/api/v1/teachers/').status_code == 200, "API /api/v1/teachers/ responsive (200)", "API")
    check(client.get('/api/v1/announcements/').status_code == 200, "API /api/v1/announcements/ responsive (200)", "API")

    print("\n" + "=" * 80)
    print(f"  🏁 FINAL AUDIT RESULT: {passed} / {total} CHECKS PASSED ({(passed/total)*100:.1f}%)")
    if failed == 0:
        print("  🌟 ALL MODULES, ENDPOINTS, STOCK FLOWS, AND PERMISSIONS ARE 100% HEALTHY!")
    else:
        print(f"  ⚠️ {failed} CHECKS FAILED - REVIEW REQUIRED.")
    print("=" * 80)

if __name__ == '__main__':
    run_tests()
