from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal
import uuid

from .models import FeeCategory, FeeStructure, StudentDiscount, FeeInvoice, FeeInvoiceItem, FeePayment
from .forms import FeeCategoryForm, FeeStructureForm, StudentDiscountForm, GenerateBulkInvoicesForm, SingleInvoiceForm, FeePaymentForm
from apps.students.models import Student
from apps.academics.models import AcademicYear, ClassRoom, Section
from apps.core.models import ActivityLog


def generate_invoice_number():
    year = timezone.now().year
    count = FeeInvoice.objects.filter(fee_year=year).count() + 1
    return f"INV-{year}-{count:05d}"


def generate_receipt_number():
    year = timezone.now().year
    count = FeePayment.objects.filter(payment_date__year=year).count() + 1
    return f"REC-{year}-{count:05d}"


@login_required
def fee_dashboard_view(request):
    """Financial and Fee Collection Dashboard"""
    today = timezone.now().date()
    current_year = today.year
    current_month_str = today.strftime('%B')

    # Quick metrics
    total_invoiced = FeeInvoice.objects.aggregate(total=Sum('payable_amount'))['total'] or Decimal('0.00')
    total_collected = FeePayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_pending = FeeInvoice.objects.filter(
        status__in=[FeeInvoice.Status.UNPAID, FeeInvoice.Status.PARTIAL, FeeInvoice.Status.OVERDUE]
    ).aggregate(total=Sum('balance_amount'))['total'] or Decimal('0.00')
    
    today_collected = FeePayment.objects.filter(payment_date=today).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_collected = FeePayment.objects.filter(
        payment_date__year=current_year,
        payment_date__month=today.month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Defaulters count (overdue invoices)
    defaulters_count = FeeInvoice.objects.filter(
        due_date__lt=today,
        status__in=[FeeInvoice.Status.UNPAID, FeeInvoice.Status.PARTIAL, FeeInvoice.Status.OVERDUE]
    ).values('student').distinct().count()

    # Recent payments
    recent_payments = FeePayment.objects.select_related('student', 'invoice', 'received_by')[:10]

    # Recent invoices
    recent_invoices = FeeInvoice.objects.select_related('student', 'class_room')[:10]

    context = {
        'page_title': 'Fee Management & Accounts',
        'total_invoiced': total_invoiced,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'today_collected': today_collected,
        'month_collected': month_collected,
        'defaulters_count': defaulters_count,
        'recent_payments': recent_payments,
        'recent_invoices': recent_invoices,
    }
    return render(request, 'fees/fee_dashboard.html', context)


@login_required
def invoice_list_view(request):
    """List and filter student fee invoices / challans"""
    invoices = FeeInvoice.objects.select_related('student', 'class_room', 'section', 'academic_year')

    status_filter = request.GET.get('status', '')
    class_filter = request.GET.get('class_room', '')
    month_filter = request.GET.get('fee_month', '')
    query = request.GET.get('q', '').strip()

    if status_filter:
        invoices = invoices.filter(status=status_filter)
    if class_filter:
        invoices = invoices.filter(class_room_id=class_filter)
    if month_filter:
        invoices = invoices.filter(fee_month__icontains=month_filter)
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(student__admission_number__icontains=query) |
            Q(student__guardian_phone__icontains=query)
        )

    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    classes = ClassRoom.objects.all()

    context = {
        'page_title': 'Fee Invoices & Challans',
        'page_obj': page_obj,
        'classes': classes,
        'status_filter': status_filter,
        'class_filter': class_filter,
        'month_filter': month_filter,
        'query': query,
    }
    return render(request, 'fees/invoice_list.html', context)


@login_required
def invoice_detail_view(request, pk):
    """View details of a single fee invoice"""
    invoice = get_object_or_404(FeeInvoice.objects.select_related('student', 'class_room', 'section', 'academic_year'), pk=pk)
    items = invoice.items.select_related('fee_category')
    payments = invoice.payments.select_related('received_by').all()

    context = {
        'page_title': f"Invoice #{invoice.invoice_number}",
        'invoice': invoice,
        'items': items,
        'payments': payments,
    }
    return render(request, 'fees/invoice_detail.html', context)


@login_required
def generate_bulk_invoices_view(request):
    """Bulk generate monthly fee challans for a class or entire school"""
    if request.method == 'POST':
        form = GenerateBulkInvoicesForm(request.POST)
        if form.is_valid():
            academic_year = form.cleaned_data['academic_year']
            class_room = form.cleaned_data.get('class_room')
            fee_month = form.cleaned_data['fee_month']
            fee_year = form.cleaned_data['fee_year']
            issue_date = form.cleaned_data['issue_date']
            due_date = form.cleaned_data['due_date']
            apply_discounts = form.cleaned_data.get('apply_discounts', True)

            # Select target students
            students_qs = Student.objects.filter(status='ACTIVE')
            if class_room:
                students_qs = students_qs.filter(current_class=class_room)

            created_count = 0
            skipped_count = 0

            for student in students_qs:
                # Check if invoice already exists for this month & year
                existing = FeeInvoice.objects.filter(
                    student=student,
                    fee_month=fee_month,
                    fee_year=fee_year
                ).exists()

                if existing:
                    skipped_count += 1
                    continue

                # Find fee structures for student's class
                structures = FeeStructure.objects.filter(
                    academic_year=academic_year,
                    class_room=student.current_class
                )

                if not structures.exists():
                    # Fallback default tuition fee if structure not explicitly defined
                    subtotal = Decimal('3000.00')
                    items_to_create = [('Monthly Tuition Fee', None, subtotal)]
                else:
                    subtotal = sum(s.amount for s in structures)
                    items_to_create = [(s.fee_category.name, s.fee_category, s.amount) for s in structures]

                # Check discounts
                discount_amount = Decimal('0.00')
                if apply_discounts:
                    discounts = student.fee_discounts.filter(is_active=True)
                    for d in discounts:
                        if d.discount_type == StudentDiscount.DiscountType.PERCENTAGE:
                            discount_amount += (subtotal * (d.value / Decimal('100.00')))
                        else:
                            discount_amount += d.value

                discount_amount = min(discount_amount, subtotal)
                payable = max(Decimal('0.00'), subtotal - discount_amount)

                # Create Invoice
                inv_number = generate_invoice_number()
                invoice = FeeInvoice.objects.create(
                    invoice_number=inv_number,
                    student=student,
                    academic_year=academic_year,
                    class_room=student.current_class,
                    section=student.current_section,
                    fee_month=fee_month,
                    fee_year=fee_year,
                    issue_date=issue_date,
                    due_date=due_date,
                    subtotal_amount=subtotal,
                    discount_amount=discount_amount,
                    fine_amount=Decimal('0.00'),
                    payable_amount=payable,
                    paid_amount=Decimal('0.00'),
                    balance_amount=payable,
                    status=FeeInvoice.Status.UNPAID,
                    created_by=request.user
                )

                # Create items
                default_cat = FeeCategory.objects.first()
                for name, cat, amt in items_to_create:
                    FeeInvoiceItem.objects.create(
                        invoice=invoice,
                        fee_category=cat or default_cat,
                        description=name,
                        amount=amt
                    )

                created_count += 1

            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Fees',
                description=f"Bulk generated {created_count} fee challans for {fee_month} {fee_year}."
            )

            messages.success(request, f"Successfully generated {created_count} invoices for '{fee_month} {fee_year}'. ({skipped_count} already existed and were skipped).")
            return redirect('fees:invoice_list')
    else:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        today = timezone.now().date()
        next_due = today.replace(day=10) if today.day <= 10 else today
        form = GenerateBulkInvoicesForm(initial={
            'academic_year': current_year,
            'fee_month': today.strftime('%B %Y'),
            'fee_year': today.year,
            'issue_date': today,
            'due_date': next_due,
            'apply_discounts': True
        })

    return render(request, 'fees/bulk_generate.html', {
        'form': form,
        'page_title': 'Generate Monthly Fee Challans'
    })


@login_required
def create_single_invoice_view(request):
    """Create a single customized fee invoice"""
    if request.method == 'POST':
        form = SingleInvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.invoice_number = generate_invoice_number()
            invoice.created_by = request.user
            
            # Read line items from POST
            item_names = request.POST.getlist('item_name[]')
            item_amounts = request.POST.getlist('item_amount[]')
            item_categories = request.POST.getlist('item_category[]')
            
            subtotal = Decimal('0.00')
            valid_items = []
            for name, amt_str, cat_id in zip(item_names, item_amounts, item_categories):
                if name.strip() and amt_str.strip():
                    try:
                        amt = Decimal(amt_str)
                        cat = FeeCategory.objects.filter(id=cat_id).first() if cat_id else FeeCategory.objects.first()
                        valid_items.append((name.strip(), cat, amt))
                        subtotal += amt
                    except Exception:
                        pass
            
            discount_str = request.POST.get('discount_amount', '0')
            fine_str = request.POST.get('fine_amount', '0')
            discount = Decimal(discount_str) if discount_str else Decimal('0.00')
            fine = Decimal(fine_str) if fine_str else Decimal('0.00')

            payable = max(Decimal('0.00'), (subtotal - discount) + fine)
            
            invoice.subtotal_amount = subtotal
            invoice.discount_amount = discount
            invoice.fine_amount = fine
            invoice.payable_amount = payable
            invoice.balance_amount = payable
            invoice.status = FeeInvoice.Status.UNPAID
            invoice.save()

            # Create items
            for name, cat, amt in valid_items:
                FeeInvoiceItem.objects.create(
                    invoice=invoice,
                    fee_category=cat or FeeCategory.objects.first(),
                    description=name,
                    amount=amt
                )

            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Fees',
                description=f"Created custom invoice #{invoice.invoice_number} for {invoice.student.get_full_name()} (Rs. {payable})"
            )

            messages.success(request, f"Invoice #{invoice.invoice_number} generated successfully.")
            return redirect('fees:invoice_detail', pk=invoice.pk)
    else:
        current_year = AcademicYear.objects.filter(is_current=True).first()
        today = timezone.now().date()
        student_id = request.GET.get('student')
        initial = {
            'academic_year': current_year,
            'fee_month': today.strftime('%B %Y'),
            'fee_year': today.year,
            'issue_date': today,
            'due_date': today,
        }
        if student_id:
            st = Student.objects.filter(pk=student_id).first()
            if st:
                initial['student'] = st
                initial['class_room'] = st.current_class
                initial['section'] = st.current_section
        form = SingleInvoiceForm(initial=initial)

    categories = FeeCategory.objects.filter(is_active=True)
    return render(request, 'fees/invoice_form.html', {
        'form': form,
        'categories': categories,
        'page_title': 'Create Single Fee Challan'
    })


@login_required
def collect_payment_view(request, invoice_id=None):
    """Collect payment against a fee invoice"""
    invoice = None
    if invoice_id:
        invoice = get_object_or_404(FeeInvoice, pk=invoice_id)
    
    if request.method == 'POST':
        target_inv_id = request.POST.get('invoice_id') or invoice_id
        target_invoice = get_object_or_404(FeeInvoice, pk=target_inv_id)
        
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.receipt_number = generate_receipt_number()
            payment.invoice = target_invoice
            payment.student = target_invoice.student
            payment.received_by = request.user
            payment.save()

            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Fees',
                description=f"Collected Rs. {payment.amount} for invoice #{target_invoice.invoice_number} from {payment.student.get_full_name()}."
            )

            messages.success(request, f"Payment of Rs. {payment.amount} recorded! Receipt #{payment.receipt_number} issued.")
            return redirect('fees:payment_receipt', pk=payment.pk)
    else:
        initial = {
            'payment_date': timezone.now().date(),
            'amount': invoice.balance_amount if invoice else Decimal('0.00'),
        }
        form = FeePaymentForm(initial=initial)

    # Search for pending invoices if none selected
    pending_invoices = None
    search_q = request.GET.get('q', '').strip()
    if search_q and not invoice:
        pending_invoices = FeeInvoice.objects.filter(
            Q(student__first_name__icontains=search_q) |
            Q(student__last_name__icontains=search_q) |
            Q(student__admission_number__icontains=search_q) |
            Q(invoice_number__icontains=search_q)
        ).exclude(status=FeeInvoice.Status.PAID)[:10]

    return render(request, 'fees/collect_payment.html', {
        'invoice': invoice,
        'form': form,
        'pending_invoices': pending_invoices,
        'search_q': search_q,
        'page_title': 'Collect Fee Payment'
    })


@login_required
def payment_receipt_view(request, pk):
    """Printable official fee receipt / voucher"""
    payment = get_object_or_404(FeePayment.objects.select_related('student', 'invoice', 'received_by'), pk=pk)
    invoice = payment.invoice

    context = {
        'page_title': f"Receipt #{payment.receipt_number}",
        'payment': payment,
        'invoice': invoice,
    }
    return render(request, 'fees/payment_receipt.html', context)


@login_required
def student_ledger_view(request, student_id):
    """Complete financial ledger and 12-month Jan-Dec payment matrix for a student"""
    student = get_object_or_404(Student.objects.select_related('current_class', 'current_section', 'academic_year'), pk=student_id)
    invoices = student.fee_invoices.all().order_by('issue_date')
    payments = student.fee_payments.all().order_by('payment_date')

    # Summary metrics
    total_billed = invoices.aggregate(total=Sum('payable_amount'))['total'] or Decimal('0.00')
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_dues = max(Decimal('0.00'), total_billed - total_paid)

    # Build chronological timeline ledger
    timeline = []
    running_balance = Decimal('0.00')

    # Combine invoices (debit) and payments (credit)
    events = []
    for inv in invoices:
        events.append({
            'date': inv.issue_date,
            'type': 'DEBIT',
            'desc': f"Fee Invoice #{inv.invoice_number} ({inv.fee_month})",
            'debit': inv.payable_amount,
            'credit': Decimal('0.00'),
            'obj': inv
        })
    for pay in payments:
        events.append({
            'date': pay.payment_date,
            'type': 'CREDIT',
            'desc': f"Payment Received: Receipt #{pay.receipt_number} ({pay.get_payment_method_display()})",
            'debit': Decimal('0.00'),
            'credit': pay.amount,
            'obj': pay
        })

    events.sort(key=lambda x: x['date'])

    for ev in events:
        running_balance += (ev['debit'] - ev['credit'])
        ev['balance'] = running_balance
        timeline.append(ev)

    # 12 Months matrix for current year
    year = timezone.now().year
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    month_matrix = []
    for m in month_names:
        inv = invoices.filter(fee_month__icontains=m, fee_year=year).first()
        status = 'NO_INVOICE'
        if inv:
            status = inv.status
        month_matrix.append({'name': m, 'status': status, 'invoice': inv})

    context = {
        'page_title': f"Fee Ledger - {student.get_full_name()}",
        'student': student,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'total_dues': total_dues,
        'timeline': timeline,
        'month_matrix': month_matrix,
        'year': year,
    }
    return render(request, 'fees/student_ledger.html', context)


@login_required
def fee_defaulters_view(request):
    """List of students with overdue or pending fees"""
    today = timezone.now().date()
    class_filter = request.GET.get('class_room', '')
    
    overdue_invoices = FeeInvoice.objects.filter(
        status__in=[FeeInvoice.Status.UNPAID, FeeInvoice.Status.PARTIAL, FeeInvoice.Status.OVERDUE],
        due_date__lt=today
    ).select_related('student', 'class_room', 'section')

    if class_filter:
        overdue_invoices = overdue_invoices.filter(class_room_id=class_filter)

    # Group by student
    total_defaulter_amount = overdue_invoices.aggregate(total=Sum('balance_amount'))['total'] or Decimal('0.00')
    classes = ClassRoom.objects.all()

    context = {
        'page_title': 'Fee Defaulters & Pending Dues',
        'overdue_invoices': overdue_invoices,
        'total_defaulter_amount': total_defaulter_amount,
        'classes': classes,
        'class_filter': class_filter,
    }
    return render(request, 'fees/defaulters_list.html', context)


@login_required
def fee_structures_view(request):
    """Manage class-wise fee structures and categories"""
    categories = FeeCategory.objects.all()
    structures = FeeStructure.objects.select_related('class_room', 'fee_category', 'academic_year')
    current_year = AcademicYear.objects.filter(is_current=True).first()

    if request.method == 'POST' and 'create_category' in request.POST:
        cat_form = FeeCategoryForm(request.POST)
        if cat_form.is_valid():
            cat_form.save()
            messages.success(request, "Fee Category added successfully.")
            return redirect('fees:fee_structures')
    elif request.method == 'POST' and 'create_structure' in request.POST:
        struct_form = FeeStructureForm(request.POST)
        if struct_form.is_valid():
            struct_form.save()
            messages.success(request, "Class Fee Structure configured.")
            return redirect('fees:fee_structures')
    else:
        cat_form = FeeCategoryForm()
        struct_form = FeeStructureForm(initial={'academic_year': current_year})

    context = {
        'page_title': 'Class Fee Structures & Categories',
        'categories': categories,
        'structures': structures,
        'cat_form': cat_form,
        'struct_form': struct_form,
    }
    return render(request, 'fees/fee_structures.html', context)


@login_required
def student_discounts_view(request):
    """Manage student fee concessions and scholarships"""
    discounts = StudentDiscount.objects.select_related('student', 'fee_category')
    
    if request.method == 'POST':
        form = StudentDiscountForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student scholarship / discount recorded.")
            return redirect('fees:student_discounts')
    else:
        form = StudentDiscountForm()

    context = {
        'page_title': 'Scholarships & Fee Concessions',
        'discounts': discounts,
        'form': form,
    }
    return render(request, 'fees/student_discounts.html', context)
