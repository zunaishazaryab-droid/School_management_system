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
from apps.accounts.decorators import accountant_required, teacher_required
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


def get_students_annual_fee_records(students_queryset, year=None):
    """Helper to compile 12-month Jan to Dec fee matrix, total billed, paid & balance for students"""
    if not year:
        year = timezone.now().year
    
    today = timezone.now().date()
    current_month_name = today.strftime('%B')
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    full_month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    records = []
    for student in students_queryset:
        invoices = list(student.fee_invoices.filter(fee_year=year).order_by('issue_date'))
        payments = list(student.fee_payments.filter(payment_date__year=year).order_by('payment_date'))
        
        total_billed = sum((inv.payable_amount for inv in invoices), Decimal('0.00'))
        total_paid = sum((p.amount for p in payments), Decimal('0.00'))
        total_dues = max(Decimal('0.00'), total_billed - total_paid)
        
        # 12 months map & friendly lists
        months_data = []
        paid_months = []
        unpaid_months = []
        partial_months = []
        
        for short_m, full_m in zip(month_names, full_month_names):
            inv = next((i for i in invoices if full_m.lower() in i.fee_month.lower() or short_m.lower() in i.fee_month.lower()), None)
            if not inv:
                months_data.append({
                    'short': short_m,
                    'full': full_m,
                    'status': 'NO_INVOICE',
                    'payable': Decimal('0.00'),
                    'paid': Decimal('0.00'),
                    'balance': Decimal('0.00'),
                    'invoice': None
                })
            else:
                m_info = {
                    'short': short_m,
                    'full': full_m,
                    'status': inv.status,
                    'payable': inv.payable_amount,
                    'paid': inv.paid_amount,
                    'balance': inv.balance_amount,
                    'invoice': inv
                }
                months_data.append(m_info)
                
                if inv.status == FeeInvoice.Status.PAID:
                    paid_months.append(f"{full_m} (Rs. {int(inv.paid_amount)})")
                elif inv.status == FeeInvoice.Status.PARTIAL:
                    partial_months.append(f"{full_m} (Due: Rs. {int(inv.balance_amount)})")
                else:
                    unpaid_months.append(f"{full_m} (Due: Rs. {int(inv.payable_amount)})")
                
        # Current month specific status
        current_m_inv = next((i for i in invoices if current_month_name.lower() in i.fee_month.lower()), None)
        
        records.append({
            'student': student,
            'total_billed': total_billed,
            'total_paid': total_paid,
            'total_dues': total_dues,
            'months': months_data,
            'paid_months': paid_months,
            'unpaid_months': unpaid_months,
            'partial_months': partial_months,
            'current_month_name': current_month_name,
            'current_m_inv': current_m_inv,
            'invoice_count': len(invoices),
        })
    return records


@login_required
def fee_dashboard_view(request):
    """Financial and Fee Collection Dashboard"""
    if getattr(request.user, 'is_student', False) or getattr(request.user, 'is_parent', False):
        return redirect('students:student_dashboard')

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

    # Recent payments (up to 20 for rich inline editing)
    recent_payments = FeePayment.objects.select_related('student', 'invoice', 'received_by')[:20]

    # Recent invoices
    recent_invoices = FeeInvoice.objects.select_related('student', 'class_room')[:15]

    # Students Annual Fee Records (All Active Students with 12 Months Matrix)
    students_qs = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section').prefetch_related('fee_invoices', 'fee_payments')
    annual_student_records = get_students_annual_fee_records(students_qs, year=current_year)

    # Pending invoices for quick collection drawer / modal (only invoices with real due balance > 0)
    pending_invoices = FeeInvoice.objects.exclude(status=FeeInvoice.Status.PAID).filter(balance_amount__gt=0).select_related('student', 'class_room').order_by('-due_date', '-id')[:100]

    # All active students for direct quick payment collection
    all_active_students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section').order_by('current_class__numeric_level', 'first_name')

    payment_methods = FeePayment.PaymentMethod.choices
    fee_months_options = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

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
        'annual_student_records': annual_student_records,
        'pending_invoices': pending_invoices,
        'all_active_students': all_active_students,
        'fee_months_options': fee_months_options,
        'payment_methods': payment_methods,
        'today': today,
        'current_year': current_year,
    }
    return render(request, 'fees/fee_dashboard.html', context)


@login_required
def invoice_list_view(request):
    """List and filter student fee invoices / challans"""
    invoices = FeeInvoice.objects.select_related('student', 'class_room', 'section', 'academic_year')

    if getattr(request.user, 'is_student', False):
        student_obj = getattr(request.user, 'student_profile', None)
        if student_obj:
            invoices = invoices.filter(student=student_obj)
        else:
            invoices = invoices.none()
    else:
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
        'status_filter': request.GET.get('status', ''),
        'class_filter': request.GET.get('class_room', ''),
        'month_filter': request.GET.get('fee_month', ''),
        'query': request.GET.get('q', '').strip(),
    }
    return render(request, 'fees/invoice_list.html', context)


@login_required
def invoice_detail_view(request, pk):
    """View details of a single fee invoice"""
    invoice = get_object_or_404(FeeInvoice.objects.select_related('student', 'class_room', 'section', 'academic_year'), pk=pk)
    if getattr(request.user, 'is_student', False):
        if hasattr(request.user, 'student_profile') and invoice.student != request.user.student_profile:
            messages.error(request, "Unauthorized access to fee invoice.")
            return redirect('students:student_dashboard')

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
@accountant_required
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
@teacher_required
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
@teacher_required
def invoice_edit_view(request, pk):
    """Edit existing fee invoice, fee items, discounts, or due date"""
    invoice = get_object_or_404(FeeInvoice.objects.select_related('student', 'class_room', 'academic_year'), pk=pk)
    
    if request.method == 'POST':
        form = SingleInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            invoice = form.save(commit=False)
            
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
            balance = max(Decimal('0.00'), payable - invoice.paid_amount)
            
            invoice.subtotal_amount = subtotal
            invoice.discount_amount = discount
            invoice.fine_amount = fine
            invoice.payable_amount = payable
            invoice.balance_amount = balance
            
            if balance == Decimal('0.00') and payable > 0:
                invoice.status = FeeInvoice.Status.PAID
            elif invoice.paid_amount > 0:
                invoice.status = FeeInvoice.Status.PARTIAL
            else:
                invoice.status = FeeInvoice.Status.UNPAID
            invoice.save()
            
            # Replace items
            invoice.items.all().delete()
            for name, cat, amt in valid_items:
                FeeInvoiceItem.objects.create(
                    invoice=invoice,
                    fee_category=cat or FeeCategory.objects.first(),
                    description=name,
                    amount=amt
                )
            
            ActivityLog.log_activity(
                user=request.user,
                action='UPDATE',
                module='Fees',
                description=f"Updated fee invoice #{invoice.invoice_number} for {invoice.student.get_full_name()} (Payable: Rs. {payable})"
            )
            
            messages.success(request, f"Fee Invoice #{invoice.invoice_number} updated successfully!")
            return redirect('fees:invoice_detail', pk=invoice.pk)
    else:
        form = SingleInvoiceForm(instance=invoice)
    
    categories = FeeCategory.objects.filter(is_active=True)
    existing_items = list(invoice.items.all())
    
    return render(request, 'fees/invoice_form.html', {
        'form': form,
        'invoice': invoice,
        'is_edit': True,
        'existing_items': existing_items,
        'categories': categories,
        'page_title': f"Edit Fee Invoice #{invoice.invoice_number}"
    })


@login_required
@teacher_required
def collect_payment_view(request, invoice_id=None):
    """Collect payment against a fee invoice or directly for a student and fee month"""
    invoice = None
    if invoice_id:
        invoice = get_object_or_404(FeeInvoice.objects.select_related('student', 'class_room'), pk=invoice_id)
    
    if request.method == 'POST':
        target_inv_id = request.POST.get('invoice_id') or invoice_id
        student_id = request.POST.get('student_id')
        fee_month = request.POST.get('fee_month')
        amount_str = request.POST.get('amount', '').strip()
        payment_date = request.POST.get('payment_date') or timezone.now().date()
        payment_method = request.POST.get('payment_method', FeePayment.PaymentMethod.CASH)
        transaction_reference = request.POST.get('transaction_reference', '').strip()
        remarks = request.POST.get('remarks', '').strip()
        next_url = request.POST.get('next', '').strip()

        try:
            amount = Decimal(amount_str) if amount_str else Decimal('0.00')
        except Exception:
            amount = Decimal('0.00')

        if amount <= Decimal('0.00'):
            messages.error(request, "Please enter a valid payment amount greater than zero.")
            return redirect(next_url or 'fees:fee_dashboard')

        target_invoice = None
        if target_inv_id:
            target_invoice = get_object_or_404(FeeInvoice, pk=target_inv_id)
        elif student_id:
            student = get_object_or_404(Student, pk=student_id)
            if not fee_month:
                fee_month = f"{timezone.now().strftime('%B')} {timezone.now().year}"
            
            # Check if invoice already exists for this student and month
            target_invoice = FeeInvoice.objects.filter(student=student, fee_month__iexact=fee_month).first()
            if not target_invoice:
                # Create a fresh on-the-fly invoice for this student & month
                academic_year = student.academic_year or AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.first()
                target_invoice = FeeInvoice.objects.create(
                    invoice_number=generate_invoice_number(),
                    student=student,
                    academic_year=academic_year,
                    class_room=student.current_class,
                    section=student.current_section,
                    fee_month=fee_month,
                    fee_year=timezone.now().year,
                    issue_date=timezone.now().date(),
                    due_date=timezone.now().date(),
                    subtotal_amount=amount,
                    discount_amount=Decimal('0.00'),
                    fine_amount=Decimal('0.00'),
                    payable_amount=amount,
                    paid_amount=Decimal('0.00'),
                    balance_amount=amount,
                    status=FeeInvoice.Status.UNPAID,
                    created_by=request.user
                )
                cat = FeeCategory.objects.filter(code='TUI').first() or FeeCategory.objects.first()
                FeeInvoiceItem.objects.create(
                    invoice=target_invoice,
                    fee_category=cat,
                    description=f"Monthly Tuition Fee ({fee_month})",
                    amount=amount
                )

        if not target_invoice:
            messages.error(request, "Please select a student or a fee invoice to record payment.")
            return redirect(next_url or 'fees:fee_dashboard')

        # Create the payment record
        payment = FeePayment.objects.create(
            receipt_number=generate_receipt_number(),
            invoice=target_invoice,
            student=target_invoice.student,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            remarks=remarks,
            received_by=request.user
        )

        ActivityLog.log_activity(
            user=request.user,
            action='CREATE',
            module='Fees',
            description=f"Collected Rs. {payment.amount} for {target_invoice.student.get_full_name()} ({target_invoice.fee_month}) via {payment.get_payment_method_display()}."
        )

        messages.success(request, f"Payment of Rs. {payment.amount} successfully recorded for {target_invoice.student.get_full_name()}! Receipt #{payment.receipt_number} issued.")
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
    if not invoice:
        if search_q:
            pending_invoices = FeeInvoice.objects.filter(
                Q(student__first_name__icontains=search_q) |
                Q(student__last_name__icontains=search_q) |
                Q(student__admission_number__icontains=search_q) |
                Q(invoice_number__icontains=search_q)
            ).exclude(status=FeeInvoice.Status.PAID).filter(balance_amount__gt=0).select_related('student', 'class_room')[:15]
        else:
            pending_invoices = FeeInvoice.objects.exclude(status=FeeInvoice.Status.PAID).filter(balance_amount__gt=0).select_related('student', 'class_room').order_by('-id')[:12]

    all_students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section').order_by('current_class__numeric_level', 'first_name')
    fee_months_options = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    return render(request, 'fees/collect_payment.html', {
        'invoice': invoice,
        'form': form,
        'pending_invoices': pending_invoices,
        'all_students': all_students,
        'fee_months_options': fee_months_options,
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
    if getattr(request.user, 'is_student', False):
        if hasattr(request.user, 'student_profile') and student != request.user.student_profile:
            messages.error(request, "Unauthorized access to student fee ledger.")
            return redirect('students:student_dashboard')

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
@accountant_required
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
@accountant_required
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
@accountant_required
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


@login_required
def fee_challan_3part_view(request, pk):
    """Render authentic 3-part (Bank, School, Student) printable Fee Challan voucher."""
    invoice = get_object_or_404(FeeInvoice.objects.select_related('student', 'student__current_class', 'student__current_section', 'academic_year'), pk=pk)
    if getattr(request.user, 'is_student', False):
        if hasattr(request.user, 'student_profile') and invoice.student != request.user.student_profile:
            messages.error(request, "Unauthorized access to fee challan.")
            return redirect('students:student_dashboard')

    items = invoice.items.all()
    
    copies = [
        {'title': 'BANK COPY', 'badge_bg': '#e0f2fe', 'badge_color': '#0369a1'},
        {'title': 'SCHOOL COPY', 'badge_bg': '#fef3c7', 'badge_color': '#92400e'},
        {'title': 'STUDENT / PARENT COPY', 'badge_bg': '#dcfce7', 'badge_color': '#166534'}
    ]

    return render(request, 'fees/fee_challan_3part.html', {
        'invoice': invoice,
        'items': items,
        'copies': copies,
        'page_title': f"3-Part Fee Challan - {invoice.invoice_number}"
    })


@login_required
@teacher_required
def payment_edit_view(request, pk):
    """Edit an existing fee payment receipt and recalculate invoice balance"""
    payment = get_object_or_404(FeePayment.objects.select_related('student', 'invoice'), pk=pk)
    invoice = payment.invoice
    
    if request.method == 'POST':
        form = FeePaymentForm(request.POST, instance=payment)
        if form.is_valid():
            saved_payment = form.save()
            
            ActivityLog.log_activity(
                user=request.user,
                action='UPDATE',
                module='Fees',
                description=f"Updated payment receipt #{saved_payment.receipt_number} for {saved_payment.student.get_full_name()} (New Amount: Rs. {saved_payment.amount})"
            )
            messages.success(request, f"Payment Receipt #{saved_payment.receipt_number} updated successfully! Invoice balance synchronized.")
            
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('fees:fee_dashboard')
    else:
        form = FeePaymentForm(instance=payment)
        
    return render(request, 'fees/payment_edit.html', {
        'payment': payment,
        'invoice': invoice,
        'form': form,
        'page_title': f"Edit Payment Receipt #{payment.receipt_number}"
    })


@login_required
@teacher_required
def payment_delete_view(request, pk):
    """Delete a fee payment receipt and restore invoice balance"""
    payment = get_object_or_404(FeePayment.objects.select_related('student', 'invoice'), pk=pk)
    receipt_no = payment.receipt_number
    student_name = payment.student.get_full_name()
    amount = payment.amount
    invoice = payment.invoice

    if request.method == 'POST':
        payment.delete()
        if invoice:
            invoice.recalculate_totals()
            
        ActivityLog.log_activity(
            user=request.user,
            action='DELETE',
            module='Fees',
            description=f"Deleted payment receipt #{receipt_no} of Rs. {amount} for {student_name}"
        )
        messages.success(request, f"Payment receipt #{receipt_no} (Rs. {amount}) was deleted and invoice #{invoice.invoice_number} balance restored.")
        
        next_url = request.POST.get('next') or request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('fees:fee_dashboard')
        
    return render(request, 'fees/payment_confirm_delete.html', {
        'payment': payment,
        'invoice': invoice,
        'page_title': f"Delete Payment Receipt #{receipt_no}"
    })


@login_required
@teacher_required
def invoice_delete_view(request, pk):
    """Delete a fee invoice and log activity"""
    invoice = get_object_or_404(FeeInvoice.objects.select_related('student'), pk=pk)
    inv_number = invoice.invoice_number
    student_name = invoice.student.get_full_name()

    if request.method == 'POST':
        invoice.delete()
        ActivityLog.log_activity(
            user=request.user,
            action='DELETE',
            module='Fees',
            description=f"Deleted fee invoice #{inv_number} for {student_name}"
        )
        messages.success(request, f"Fee Invoice #{inv_number} was deleted successfully.")
        return redirect('fees:invoice_list')
        
    return render(request, 'fees/invoice_confirm_delete.html', {
        'invoice': invoice,
        'page_title': f"Delete Invoice #{inv_number}"
    })


@login_required
def student_annual_records_view(request):
    """Annual Student Fee Records Directory with 12-Month Jan-Dec Matrix"""
    if getattr(request.user, 'is_student', False) or getattr(request.user, 'is_parent', False):
        return redirect('students:student_dashboard')

    year = int(request.GET.get('year', timezone.now().year))
    class_id = request.GET.get('class_room', '')
    query = request.GET.get('q', '').strip()
    
    students = Student.objects.filter(status='ACTIVE').select_related('current_class', 'current_section').prefetch_related('fee_invoices', 'fee_payments')
    
    if class_id:
        students = students.filter(current_class_id=class_id)
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(roll_number__icontains=query) |
            Q(guardian_phone__icontains=query)
        )
        
    annual_records = get_students_annual_fee_records(students, year=year)
    available_years = list(range(2026, 2051))
    classes = ClassRoom.objects.all()
    
    context = {
        'page_title': f'Annual Student Fee Records ({year})',
        'year': year,
        'available_years': available_years,
        'annual_records': annual_records,
        'classes': classes,
        'selected_class': class_id,
        'query': query,
    }
    return render(request, 'fees/student_annual_records.html', context)


@login_required
def student_annual_card_view(request, student_id):
    """Official 12-Month Printable Annual Student Fee Card / Ledger"""
    student = get_object_or_404(Student.objects.select_related('current_class', 'current_section', 'academic_year'), pk=student_id)
    if getattr(request.user, 'is_student', False):
        if hasattr(request.user, 'student_profile') and student != request.user.student_profile:
            messages.error(request, "Unauthorized access to student fee card.")
            return redirect('students:student_dashboard')

    year = int(request.GET.get('year', timezone.now().year))
    
    invoices = student.fee_invoices.filter(fee_year=year).order_by('issue_date')
    payments = student.fee_payments.filter(payment_date__year=year).order_by('payment_date')
    
    total_billed = sum((inv.payable_amount for inv in invoices), Decimal('0.00'))
    total_paid = sum((p.amount for p in payments), Decimal('0.00'))
    total_concessions = sum((inv.discount_amount for inv in invoices), Decimal('0.00'))
    total_dues = max(Decimal('0.00'), total_billed - total_paid)
    
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    annual_breakdown = []
    for month_name in month_names:
        inv = invoices.filter(Q(fee_month__icontains=month_name) | Q(fee_month__icontains=month_name[:3])).first()
        if inv:
            month_payments = list(inv.payments.all())
            receipt_nums = ", ".join([p.receipt_number for p in month_payments]) if month_payments else "--"
            last_pay_date = month_payments[-1].payment_date if month_payments else None
            
            annual_breakdown.append({
                'month': month_name,
                'invoice': inv,
                'invoice_number': inv.invoice_number,
                'due_date': inv.due_date,
                'subtotal': inv.subtotal_amount,
                'discount': inv.discount_amount,
                'fine': inv.fine_amount,
                'payable': inv.payable_amount,
                'paid': inv.paid_amount,
                'balance': inv.balance_amount,
                'status': inv.status,
                'receipt_numbers': receipt_nums,
                'payment_date': last_pay_date,
                'payments': month_payments
            })
        else:
            annual_breakdown.append({
                'month': month_name,
                'invoice': None,
                'invoice_number': '--',
                'due_date': None,
                'subtotal': Decimal('0.00'),
                'discount': Decimal('0.00'),
                'fine': Decimal('0.00'),
                'payable': Decimal('0.00'),
                'paid': Decimal('0.00'),
                'balance': Decimal('0.00'),
                'status': 'NO_INVOICE',
                'receipt_numbers': '--',
                'payment_date': None,
                'payments': []
            })
            
    available_years = list(range(2026, 2051))
    context = {
        'page_title': f"Annual Fee Card {year} - {student.get_full_name()}",
        'student': student,
        'year': year,
        'available_years': available_years,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'total_concessions': total_concessions,
        'total_dues': total_dues,
        'annual_breakdown': annual_breakdown,
        'payments': payments,
    }
    return render(request, 'fees/student_annual_card.html', context)

