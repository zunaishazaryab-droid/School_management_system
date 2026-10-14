import os
import sys
import django
from decimal import Decimal

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, r'c:\Users\hp\OneDrive\Desktop\Schoolmanagment')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Schoolmanagment.settings')
django.setup()

from django.test import Client
from apps.accounts.models import User
from apps.fees.models import FeeInvoice, FeePayment, FeeCategory, FeeInvoiceItem
from apps.students.models import Student
from apps.academics.models import AcademicYear, ClassRoom
from django.utils import timezone

print("Running Fees Direct Edit & Management QA Test...")

admin = User.objects.filter(is_superuser=True).first()
client = Client()
client.force_login(admin)

# 1. Test Dashboard loads 200
res = client.get('/fees/')
assert res.status_code == 200, f"Dashboard failed: {res.status_code}"
print("✅ Fee Dashboard loaded (200 OK)")

# 2. Find or create a test invoice & payment
student = Student.objects.filter(status='ACTIVE').first()
year = AcademicYear.objects.filter(is_current=True).first()
inv = FeeInvoice.objects.filter(student=student).first()

if not inv:
    inv = FeeInvoice.objects.create(
        invoice_number="INV-TEST-001",
        student=student,
        academic_year=year,
        class_room=student.current_class,
        fee_month="October 2026",
        fee_year=2026,
        issue_date=timezone.now().date(),
        due_date=timezone.now().date(),
        subtotal_amount=Decimal('1000.00'),
        payable_amount=Decimal('1000.00'),
        paid_amount=Decimal('0.00'),
        balance_amount=Decimal('1000.00'),
        created_by=admin
    )

# 3. Create a payment of Rs. 500
pay = FeePayment.objects.create(
    receipt_number=f"REC-TEST-{timezone.now().strftime('%M%S')}",
    invoice=inv,
    student=student,
    payment_date=timezone.now().date(),
    amount=Decimal('500.00'),
    payment_method=FeePayment.PaymentMethod.CASH,
    received_by=admin
)

inv.refresh_from_db()
print(f"Created Payment Rs. 500 -> Invoice Paid: {inv.paid_amount}, Balance: {inv.balance_amount}, Status: {inv.status}")
assert inv.paid_amount == Decimal('500.00')

# 4. Test GET payment edit page
res = client.get(f'/fees/receipts/{pay.pk}/edit/')
assert res.status_code == 200, f"Edit page failed: {res.status_code}"
print("✅ Payment Edit Page loaded (200 OK)")

# 5. POST update payment amount from Rs. 500 to Rs. 800
edit_data = {
    'amount': '800.00',
    'payment_date': pay.payment_date.strftime('%Y-%m-%d'),
    'payment_method': 'CASH',
    'transaction_reference': 'TXN-UPDATED-123',
    'remarks': 'Updated via QA Test'
}
res = client.post(f'/fees/receipts/{pay.pk}/edit/', edit_data, follow=True)
assert res.status_code == 200
inv.refresh_from_db()
pay.refresh_from_db()

print(f"Updated Payment to Rs. {pay.amount} -> Invoice Paid: {inv.paid_amount}, Balance: {inv.balance_amount}, Status: {inv.status}")
assert pay.amount == Decimal('800.00')
assert inv.paid_amount == Decimal('800.00')
print("✅ Payment Amount Edited and Invoice Recalculated accurately")

# 6. Test Payment Delete
res = client.post(f'/fees/receipts/{pay.pk}/delete/', follow=True)
assert res.status_code == 200
inv.refresh_from_db()
print(f"Deleted Payment -> Invoice Paid: {inv.paid_amount}, Balance: {inv.balance_amount}, Status: {inv.status}")
assert inv.paid_amount == Decimal('0.00')
print("✅ Payment Deleted and Invoice Balance restored successfully")

# 7. Test Student Annual Records Directory
res = client.get('/fees/annual-records/')
assert res.status_code == 200, f"Annual records failed: {res.status_code}"
print("✅ Student Annual Records Directory loaded (200 OK)")

# 8. Test Student 12-Month Annual Card View
res = client.get(f'/fees/annual-card/{student.pk}/')
assert res.status_code == 200, f"Annual Card failed: {res.status_code}"
print(f"✅ Student 12-Month Annual Fee Card loaded for {student.get_full_name()} (200 OK)")

print("\n🎉 ALL FEE ANNUAL RECORDS & DIRECT EDIT QA TESTS PASSED WITH 100% SUCCESS!")
