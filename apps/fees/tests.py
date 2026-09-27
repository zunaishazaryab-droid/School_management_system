from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date
from decimal import Decimal

from apps.accounts.models import User
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.students.models import Student
from apps.fees.models import FeeCategory, FeeStructure, StudentDiscount, FeeInvoice, FeeInvoiceItem, FeePayment


class FeeManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            password='password123',
            email='admin@school.test',
            role=User.Role.ADMIN
        )
        self.client.force_login(self.admin_user)

        self.academic_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=date(2026, 4, 1),
            end_date=date(2027, 3, 31),
            is_current=True
        )
        self.class_room = ClassRoom.objects.create(
            name='Class 5',
            code='C5',
            numeric_level=5
        )
        self.section = Section.objects.create(
            class_room=self.class_room,
            name='A'
        )
        self.student = Student.objects.create(
            admission_number='STU-2026-101',
            first_name='Zayn',
            last_name='Khan',
            current_class=self.class_room,
            current_section=self.section,
            academic_year=self.academic_year,
            admission_date=date(2026, 4, 1),
            guardian_name='Farooq Khan',
            guardian_phone='03001234567',
            residential_address='Street 1, Islamabad'
        )

        self.tuition_cat = FeeCategory.objects.create(
            name='Monthly Tuition Fee',
            code='TUI',
            default_amount=Decimal('4000.00'),
            is_recurring=True
        )

        self.structure = FeeStructure.objects.create(
            academic_year=self.academic_year,
            class_room=self.class_room,
            fee_category=self.tuition_cat,
            amount=Decimal('4000.00'),
            frequency=FeeStructure.Frequency.MONTHLY
        )

    def test_fee_dashboard_view(self):
        response = self.client.get(reverse('fees:fee_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'fees/fee_dashboard.html')

    def test_invoice_creation_and_recalculation(self):
        invoice = FeeInvoice.objects.create(
            invoice_number='INV-2026-99991',
            student=self.student,
            academic_year=self.academic_year,
            class_room=self.class_room,
            section=self.section,
            fee_month='October 2026',
            fee_year=2026,
            issue_date=date(2026, 10, 1),
            due_date=date(2026, 10, 10),
            subtotal_amount=Decimal('4000.00'),
            discount_amount=Decimal('500.00'),
            fine_amount=Decimal('0.00'),
            payable_amount=Decimal('3500.00'),
            paid_amount=Decimal('0.00'),
            balance_amount=Decimal('3500.00'),
            status=FeeInvoice.Status.UNPAID
        )

        FeeInvoiceItem.objects.create(
            invoice=invoice,
            fee_category=self.tuition_cat,
            description='Monthly Tuition October',
            amount=Decimal('4000.00')
        )

        # Make a partial payment of 2000
        payment = FeePayment.objects.create(
            receipt_number='REC-2026-99991',
            invoice=invoice,
            student=self.student,
            payment_date=date(2026, 10, 5),
            amount=Decimal('2000.00'),
            payment_method=FeePayment.PaymentMethod.CASH,
            received_by=self.admin_user
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal('2000.00'))
        self.assertEqual(invoice.balance_amount, Decimal('1500.00'))
        self.assertEqual(invoice.status, FeeInvoice.Status.PARTIAL)

        # Make remaining payment of 1500
        payment2 = FeePayment.objects.create(
            receipt_number='REC-2026-99992',
            invoice=invoice,
            student=self.student,
            payment_date=date(2026, 10, 6),
            amount=Decimal('1500.00'),
            payment_method=FeePayment.PaymentMethod.CASH,
            received_by=self.admin_user
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.paid_amount, Decimal('3500.00'))
        self.assertEqual(invoice.balance_amount, Decimal('0.00'))
        self.assertEqual(invoice.status, FeeInvoice.Status.PAID)

    def test_student_ledger_view(self):
        invoice = FeeInvoice.objects.create(
            invoice_number='INV-2026-99993',
            student=self.student,
            academic_year=self.academic_year,
            class_room=self.class_room,
            section=self.section,
            fee_month='September 2026',
            fee_year=2026,
            issue_date=date(2026, 9, 1),
            due_date=date(2026, 9, 10),
            subtotal_amount=Decimal('4000.00'),
            payable_amount=Decimal('4000.00'),
            balance_amount=Decimal('4000.00'),
            status=FeeInvoice.Status.UNPAID
        )
        response = self.client.get(reverse('fees:student_ledger', kwargs={'student_id': self.student.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'INV-2026-99993')
        self.assertContains(response, 'Zayn Khan')

    def test_receipt_view(self):
        invoice = FeeInvoice.objects.create(
            invoice_number='INV-2026-99994',
            student=self.student,
            academic_year=self.academic_year,
            class_room=self.class_room,
            section=self.section,
            fee_month='October 2026',
            fee_year=2026,
            issue_date=date(2026, 10, 1),
            due_date=date(2026, 10, 10),
            subtotal_amount=Decimal('4000.00'),
            payable_amount=Decimal('4000.00'),
            balance_amount=Decimal('4000.00'),
            status=FeeInvoice.Status.UNPAID
        )
        payment = FeePayment.objects.create(
            receipt_number='REC-2026-99994',
            invoice=invoice,
            student=self.student,
            payment_date=date(2026, 10, 2),
            amount=Decimal('4000.00'),
            payment_method=FeePayment.PaymentMethod.CASH,
            received_by=self.admin_user
        )
        response = self.client.get(reverse('fees:payment_receipt', kwargs={'pk': payment.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'REC-2026-99994')
        self.assertContains(response, 'Zayn Khan')
