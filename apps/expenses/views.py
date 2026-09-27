from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, datetime
from decimal import Decimal

from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseCategoryForm
from apps.fees.models import FeePayment, FeeInvoice
from apps.core.models import ActivityLog


def generate_expense_number():
    year = timezone.now().year
    count = Expense.objects.filter(expense_date__year=year).count() + 1
    return f"EXP-{year}-{count:05d}"


@login_required
def expense_list_view(request):
    """List, filter and search school expenses"""
    expenses = Expense.objects.select_related('category', 'recorded_by')

    category_id = request.GET.get('category', '')
    payment_method = request.GET.get('payment_method', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    query = request.GET.get('q', '').strip()

    if category_id:
        expenses = expenses.filter(category_id=category_id)
    if payment_method:
        expenses = expenses.filter(payment_method=payment_method)
    if start_date:
        expenses = expenses.filter(expense_date__gte=start_date)
    if end_date:
        expenses = expenses.filter(expense_date__lte=end_date)
    if query:
        expenses = expenses.filter(
            Q(title__icontains=query) |
            Q(payee_name__icontains=query) |
            Q(expense_number__icontains=query)
        )

    # Compute filtered total
    filtered_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Overall KPIs
    today = timezone.now().date()
    month_total = Expense.objects.filter(
        expense_date__year=today.year,
        expense_date__month=today.month,
        status=Expense.Status.PAID
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = ExpenseCategory.objects.all()

    context = {
        'page_title': 'Expense & Outflow Management',
        'page_obj': page_obj,
        'categories': categories,
        'filtered_total': filtered_total,
        'month_total': month_total,
        'category_id': category_id,
        'payment_method': payment_method,
        'start_date': start_date,
        'end_date': end_date,
        'query': query,
    }
    return render(request, 'expenses/expense_list.html', context)


@login_required
def expense_create_view(request):
    """Add new expense record"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.expense_number = generate_expense_number()
            expense.recorded_by = request.user
            expense.save()

            ActivityLog.log_activity(
                user=request.user,
                action='CREATE',
                module='Expenses',
                description=f"Recorded expense #{expense.expense_number}: {expense.title} (Rs. {expense.amount}) under {expense.category.name}"
            )

            messages.success(request, f"Expense #{expense.expense_number} recorded successfully.")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(initial={
            'expense_date': timezone.now().date(),
            'status': Expense.Status.PAID
        })

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'page_title': 'Record New Expense'
    })


@login_required
def expense_update_view(request, pk):
    """Edit existing expense record"""
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, f"Expense #{expense.expense_number} updated.")
            return redirect('expenses:expense_list')
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'expenses/expense_form.html', {
        'form': form,
        'expense': expense,
        'page_title': f"Edit Expense #{expense.expense_number}"
    })


@login_required
def expense_delete_view(request, pk):
    """Delete an expense record"""
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        num = expense.expense_number
        expense.delete()
        messages.success(request, f"Expense #{num} was deleted.")
        return redirect('expenses:expense_list')
    return render(request, 'expenses/expense_confirm_delete.html', {
        'expense': expense,
        'page_title': 'Confirm Delete Expense'
    })


@login_required
def financial_summary_view(request):
    """Income vs Expense financial overview and balance statement"""
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    # Income (Fee Payments)
    total_revenue = FeePayment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_revenue = FeePayment.objects.filter(
        payment_date__year=current_year,
        payment_date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Expenses
    total_expense = Expense.objects.filter(status=Expense.Status.PAID).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    month_expense = Expense.objects.filter(
        expense_date__year=current_year,
        expense_date__month=current_month,
        status=Expense.Status.PAID
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Net Cash Flow / Surplus
    net_surplus_total = total_revenue - total_expense
    net_surplus_month = month_revenue - month_expense

    # Category breakdown for expenses
    category_breakdown = Expense.objects.filter(
        status=Expense.Status.PAID
    ).values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    # Compute percentages
    cat_stats = []
    for item in category_breakdown:
        cat_name = item['category__name'] or 'Uncategorized'
        amt = item['total'] or Decimal('0.00')
        pct = (amt / total_expense * Decimal('100.00')) if total_expense > 0 else Decimal('0.00')
        cat_stats.append({
            'name': cat_name,
            'amount': amt,
            'count': item['count'],
            'percentage': round(pct, 1)
        })

    context = {
        'page_title': 'Financial Summary & Income vs Expense',
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'total_expense': total_expense,
        'month_expense': month_expense,
        'net_surplus_total': net_surplus_total,
        'net_surplus_month': net_surplus_month,
        'cat_stats': cat_stats,
        'current_year': current_year,
        'current_month_name': today.strftime('%B %Y'),
    }
    return render(request, 'expenses/financial_summary.html', context)


@login_required
def expense_categories_view(request):
    """Manage expense categories"""
    categories = ExpenseCategory.objects.all()
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense category added.")
            return redirect('expenses:category_list')
    else:
        form = ExpenseCategoryForm()

    return render(request, 'expenses/category_list.html', {
        'categories': categories,
        'form': form,
        'page_title': 'Expense Categories'
    })
