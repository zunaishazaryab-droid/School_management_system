from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
import random

from apps.academics.models import AcademicYear, ClassRoom
from apps.students.models import Student
from apps.accounts.models import User
from apps.fees.models import FeeCategory, FeeStructure, StudentDiscount, FeeInvoice, FeeInvoiceItem, FeePayment
from apps.expenses.models import ExpenseCategory, Expense


class Command(BaseCommand):
    help = 'Seeds realistic Sprint 3 Fee Management and Expense demo data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("[*] Starting Sprint 3 (Fees & Expenses) Seeding..."))

        admin_user = User.objects.filter(role=User.Role.ADMIN).first() or User.objects.first()
        academic_year = AcademicYear.objects.filter(is_current=True).first()

        if not academic_year:
            academic_year = AcademicYear.objects.create(
                name="2026-2027",
                start_date=date(2026, 4, 1),
                end_date=date(2027, 3, 31),
                is_current=True
            )

        # 1. Create Fee Categories
        cat_defs = [
            ("Monthly Tuition Fee", "TUI", Decimal("3500.00"), True, "Core monthly academic instructional fee"),
            ("Admission Fee", "ADM", Decimal("10000.00"), False, "One-time registration and admission processing"),
            ("Annual Charges & Development", "ANN", Decimal("6000.00"), False, "Annual maintenance, sports and events fund"),
            ("Examination Fee", "EXM", Decimal("1500.00"), False, "Term examination papers and assessment fund"),
            ("School Transport / Van", "TRN", Decimal("2500.00"), True, "Monthly school bus / van transport service"),
            ("Science & Computer Lab", "LAB", Decimal("1000.00"), True, "Practical lab equipment and IT charges"),
            ("Late Fee Fine / Surcharge", "LAT", Decimal("500.00"), False, "Penalty for payment after due date"),
        ]

        categories_map = {}
        for name, code, default_amt, is_rec, desc in cat_defs:
            cat, _ = FeeCategory.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'default_amount': default_amt,
                    'is_recurring': is_rec,
                    'description': desc,
                    'is_active': True,
                }
            )
            categories_map[code] = cat
        self.stdout.write(self.style.SUCCESS("[+] Fee Categories seeded."))

        # 2. Create Class-wise Fee Structures
        classes = ClassRoom.objects.all()
        class_base_fees = {
            "NUR": Decimal("2500.00"),
            "PREP": Decimal("2800.00"),
            "C1": Decimal("3000.00"),
            "C2": Decimal("3200.00"),
            "C3": Decimal("3500.00"),
            "C4": Decimal("3800.00"),
            "C5": Decimal("4000.00"),
            "C6": Decimal("4500.00"),
            "C7": Decimal("4800.00"),
            "C8": Decimal("5000.00"),
            "C9": Decimal("6000.00"),
            "C10": Decimal("6500.00"),
        }

        for cl in classes:
            base_amt = class_base_fees.get(cl.code, Decimal("3500.00"))
            # Tuition fee structure
            FeeStructure.objects.get_or_create(
                academic_year=academic_year,
                class_room=cl,
                fee_category=categories_map["TUI"],
                defaults={'amount': base_amt, 'frequency': FeeStructure.Frequency.MONTHLY}
            )
            # Exam fee structure
            FeeStructure.objects.get_or_create(
                academic_year=academic_year,
                class_room=cl,
                fee_category=categories_map["EXM"],
                defaults={'amount': Decimal("1500.00"), 'frequency': FeeStructure.Frequency.ANNUAL}
            )
        self.stdout.write(self.style.SUCCESS("[+] Class Fee Structures seeded."))

        # 3. Create Student Scholarships & Concessions
        active_students = list(Student.objects.filter(status='ACTIVE'))
        if active_students:
            # Assign scholarships to 3 students
            aid_defs = [
                ("Sibling / Kinship Concession (25%)", StudentDiscount.DiscountType.PERCENTAGE, Decimal("25.00")),
                ("Need-based Financial Aid (50%)", StudentDiscount.DiscountType.PERCENTAGE, Decimal("50.00")),
                ("Merit Scholarship (Full Tuition)", StudentDiscount.DiscountType.PERCENTAGE, Decimal("100.00")),
            ]
            for i, aid in enumerate(aid_defs):
                if i < len(active_students):
                    st = active_students[i]
                    StudentDiscount.objects.get_or_create(
                        student=st,
                        reason=aid[0],
                        defaults={
                            'discount_type': aid[1],
                            'value': aid[2],
                            'fee_category': categories_map["TUI"],
                            'is_active': True,
                        }
                    )
        self.stdout.write(self.style.SUCCESS("[+] Student Concessions & Scholarships seeded."))

        # 4. Generate Monthly Challans (September 2026 & October 2026) and Payments
        months_to_gen = [
            ("September 2026", 2026, date(2026, 9, 1), date(2026, 9, 10)),
            ("October 2026", 2026, date(2026, 10, 1), date(2026, 10, 10)),
        ]

        inv_counter = 1
        rec_counter = 1

        for month_name, yr, issue_dt, due_dt in months_to_gen:
            for st in active_students:
                inv_num = f"INV-{yr}-{inv_counter:05d}"
                inv_counter += 1

                # Calculate fee for student
                struct = FeeStructure.objects.filter(
                    academic_year=academic_year,
                    class_room=st.current_class,
                    fee_category=categories_map["TUI"]
                ).first()
                base_amt = struct.amount if struct else Decimal("3500.00")

                # Check discount
                disc_obj = st.fee_discounts.filter(is_active=True).first()
                discount_val = Decimal("0.00")
                if disc_obj:
                    if disc_obj.discount_type == StudentDiscount.DiscountType.PERCENTAGE:
                        discount_val = base_amt * (disc_obj.value / Decimal("100.00"))
                    else:
                        discount_val = disc_obj.value

                payable = max(Decimal("0.00"), base_amt - discount_val)

                invoice, created = FeeInvoice.objects.get_or_create(
                    student=st,
                    fee_month=month_name,
                    fee_year=yr,
                    defaults={
                        'invoice_number': inv_num,
                        'academic_year': academic_year,
                        'class_room': st.current_class,
                        'section': st.current_section,
                        'issue_date': issue_dt,
                        'due_date': due_dt,
                        'subtotal_amount': base_amt,
                        'discount_amount': discount_val,
                        'fine_amount': Decimal("0.00"),
                        'payable_amount': payable,
                        'paid_amount': Decimal("0.00"),
                        'balance_amount': payable,
                        'status': FeeInvoice.Status.UNPAID,
                        'created_by': admin_user,
                    }
                )

                if created:
                    FeeInvoiceItem.objects.create(
                        invoice=invoice,
                        fee_category=categories_map["TUI"],
                        description=f"{month_name} Monthly Tuition",
                        amount=base_amt
                    )

                    # Simulate payments
                    should_pay = False
                    if "September" in month_name:
                        should_pay = (random.random() < 0.85)
                    else:
                        should_pay = (random.random() < 0.50)

                    if should_pay and payable > 0:
                        rec_num = f"REC-{yr}-{rec_counter:05d}"
                        rec_counter += 1
                        pay_amt = payable

                        # Occasionally make partial payment
                        if random.random() < 0.20 and payable > 1000:
                            pay_amt = Decimal("2000.00")

                        FeePayment.objects.create(
                            receipt_number=rec_num,
                            invoice=invoice,
                            student=st,
                            payment_date=issue_dt + timedelta(days=random.randint(2, 8)),
                            amount=pay_amt,
                            payment_method=random.choice([
                                FeePayment.PaymentMethod.CASH,
                                FeePayment.PaymentMethod.BANK_TRANSFER,
                                FeePayment.PaymentMethod.EASYPAISA_JAZZCASH
                            ]),
                            transaction_reference=f"TXN-{random.randint(100000, 999999)}",
                            received_by=admin_user,
                            remarks="Fee payment received and cleared."
                        )

        self.stdout.write(self.style.SUCCESS("[+] Monthly Fee Invoices & Receipts generated."))

        # 5. Create Expense Categories
        exp_cat_defs = [
            ("Staff & Faculty Salaries", "SAL", "Monthly teaching and administrative staff salaries"),
            ("Campus Rent & Lease", "RNT", "Building rent and campus premises lease"),
            ("Electricity & Power Bills", "ELE", "WAPDA / IESCO electricity charges"),
            ("Gas, Water & Utilities", "UTL", "Sui gas, municipal water & sanitation"),
            ("Stationery, Printing & Exams", "STN", "Official registers, exams, report cards & stationery"),
            ("Building Maintenance & Repairs", "MNT", "Campus whitewash, plumbing, electrical repairs"),
            ("Transport Fuel & Van Maintenance", "TRN", "Van diesel, oil changes & maintenance"),
            ("Events, Sports & Functions", "EVT", "Annual sports day, Independence Day & awards"),
            ("Marketing, Banners & Admissions", "MKT", "Admission campaign, brochures & social media ads"),
            ("Miscellaneous Expenses", "MISC", "Tea, hospitality and office sundries"),
        ]

        exp_cats_map = {}
        for name, code, desc in exp_cat_defs:
            ec, _ = ExpenseCategory.objects.get_or_create(
                code=code,
                defaults={'name': name, 'description': desc, 'is_active': True}
            )
            exp_cats_map[code] = ec
        self.stdout.write(self.style.SUCCESS("[+] Expense Categories seeded."))

        # 6. Seed Realistic Expenses for Sept & Oct
        expenses_data = [
            ("Monthly Teacher Salaries (September 2026)", "SAL", Decimal("385000.00"), date(2026, 9, 5), "Teaching Staff Accounts", Expense.PaymentMethod.BANK_TRANSFER),
            ("Campus Building Rent (September)", "RNT", Decimal("120000.00"), date(2026, 9, 2), "Al-Rehman Real Estate", Expense.PaymentMethod.BANK_TRANSFER),
            ("Electricity Bill - Main Campus", "ELE", Decimal("38500.00"), date(2026, 9, 14), "IESCO Commercial", Expense.PaymentMethod.ONLINE),
            ("Printing of Term Exam Papers & Answer Sheets", "STN", Decimal("14500.00"), date(2026, 9, 18), "Al-Madina Printers", Expense.PaymentMethod.CASH),
            ("School Van Diesel & Fuel (September)", "TRN", Decimal("28000.00"), date(2026, 9, 25), "PSO Fuel Station", Expense.PaymentMethod.CASH),
            ("AC Servicing & Fan Repairs", "MNT", Decimal("8500.00"), date(2026, 9, 20), "City Electrical Services", Expense.PaymentMethod.CASH),
            ("Admission Banners & Flex Printing", "MKT", Decimal("12000.00"), date(2026, 9, 8), "Apex Media & Flex", Expense.PaymentMethod.CASH),
            ("Staff Tea, Refreshments & Hospitality", "MISC", Decimal("6500.00"), date(2026, 9, 28), "Metro Supermarket", Expense.PaymentMethod.CASH),
        ]

        for i, (title, code, amt, dt, payee, method) in enumerate(expenses_data, start=1):
            exp_num = f"EXP-2026-{i:05d}"
            Expense.objects.get_or_create(
                expense_number=exp_num,
                defaults={
                    'category': exp_cats_map[code],
                    'title': title,
                    'amount': amt,
                    'expense_date': dt,
                    'payment_method': method,
                    'payee_name': payee,
                    'recorded_by': admin_user,
                    'status': Expense.Status.PAID,
                    'remarks': f"Cleared on {dt}",
                }
            )

        self.stdout.write(self.style.SUCCESS("[+] Realistic Expenses seeded successfully."))
        self.stdout.write(self.style.SUCCESS("[*] Sprint 3 (Fees & Expenses) Seeding Complete!"))
