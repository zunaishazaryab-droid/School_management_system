from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, F, Q

from apps.accounts.decorators import accountant_required, coordinator_required
from apps.core.models import ActivityLog
from .models import InventoryItem, StockTransaction, Supplier, ItemCategory
from .forms import InventoryItemForm, StockTransactionForm, SupplierForm, ItemCategoryForm


@login_required
@accountant_required
def inventory_dashboard_view(request):
    """Inventory and asset summary dashboard - clean, simple and executive"""
    items = InventoryItem.objects.select_related('category').all()
    transactions = StockTransaction.objects.select_related('item', 'supplier').all()[:10]
    
    total_items = items.count()
    low_stock_items = [item for item in items if item.is_low_stock]
    in_stock_count = total_items - len(low_stock_items)
    total_valuation = sum((item.total_valuation for item in items), Decimal('0.00'))

    return render(request, 'inventory/inventory_dashboard.html', {
        'items': items,
        'total_items': total_items,
        'low_stock_count': len(low_stock_items),
        'in_stock_count': in_stock_count,
        'total_valuation': total_valuation,
        'recent_transactions': transactions,
        'page_title': 'School Stock & Inventory'
    })


@login_required
@accountant_required
def item_list_view(request):
    items = InventoryItem.objects.select_related('category').all()
    query = request.GET.get('q', '').strip()
    cat_id = request.GET.get('category')
    low_stock_only = request.GET.get('low_stock')

    if query:
        items = items.filter(Q(name__icontains=query) | Q(item_code__icontains=query) | Q(location__icontains=query))
    if cat_id:
        items = items.filter(category_id=cat_id)
    
    if low_stock_only:
        items = [i for i in items if i.is_low_stock]

    categories = ItemCategory.objects.all()

    return render(request, 'inventory/item_list.html', {
        'items': items,
        'categories': categories,
        'search_query': query,
        'selected_category': cat_id,
        'low_stock_only': low_stock_only,
        'page_title': 'Inventory Stock Items'
    })


@login_required
@accountant_required
def item_create_view(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            ActivityLog.log_activity(
                request.user, 'CREATE', 'Inventory',
                f"Registered inventory item '{item.name}' [{item.item_code}] with initial qty {item.quantity_in_stock}",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Item '{item.name}' added to inventory!")
            return redirect('inventory:item_list')
    else:
        form = InventoryItemForm()
    return render(request, 'inventory/item_form.html', {'form': form, 'page_title': 'Add Inventory Item', 'action': 'Add'})


@login_required
@accountant_required
def item_edit_view(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            ActivityLog.log_activity(
                request.user, 'UPDATE', 'Inventory',
                f"Updated inventory item '{item.name}' [{item.item_code}]",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Item '{item.name}' updated successfully!")
            return redirect('inventory:item_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'inventory/item_form.html', {'form': form, 'item': item, 'page_title': f'Edit Item: {item.name}', 'action': 'Edit'})


@login_required
@accountant_required
def item_delete_view(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        name = item.name
        item.delete()
        ActivityLog.log_activity(request.user, 'DELETE', 'Inventory', f"Deleted item '{name}'", request.META.get('REMOTE_ADDR'))
        messages.success(request, f"Item '{name}' deleted successfully!")
    return redirect('inventory:item_list')


@login_required
@accountant_required
def category_list_view(request):
    categories = ItemCategory.objects.all()
    if request.method == 'POST':
        form = ItemCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Category '{cat.name}' created!")
            return redirect('inventory:category_list')
    else:
        form = ItemCategoryForm()
    return render(request, 'inventory/category_list.html', {
        'categories': categories,
        'form': form,
        'page_title': 'Stock Categories'
    })


@login_required
@accountant_required
def category_delete_view(request, pk):
    cat = get_object_or_404(ItemCategory, pk=pk)
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        messages.success(request, f"Category '{name}' deleted!")
    return redirect('inventory:category_list')


@login_required
@accountant_required
def stock_transaction_list_view(request):
    transactions = StockTransaction.objects.select_related('item', 'supplier', 'created_by').all()
    tx_type = request.GET.get('type')
    if tx_type:
        transactions = transactions.filter(transaction_type=tx_type)

    return render(request, 'inventory/transaction_list.html', {
        'transactions': transactions,
        'selected_type': tx_type,
        'page_title': 'Stock In / Out Ledger'
    })


@login_required
@accountant_required
def stock_transaction_create_view(request):
    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            tx = form.save(commit=False)
            tx.created_by = request.user
            item = tx.item

            if tx.transaction_type == StockTransaction.Type.OUT:
                if item.quantity_in_stock < tx.quantity:
                    messages.error(request, f"Insufficient stock! Available: {item.quantity_in_stock} {item.get_unit_display()}, requested: {tx.quantity}")
                    return render(request, 'inventory/transaction_form.html', {'form': form, 'page_title': 'Record Stock Transaction'})
                item.quantity_in_stock -= tx.quantity
            else:
                item.quantity_in_stock += tx.quantity
                if tx.unit_price > 0:
                    item.unit_price = tx.unit_price

            item.save()
            tx.save()

            ActivityLog.log_activity(
                request.user, 'CREATE', 'Inventory',
                f"Recorded Stock {tx.transaction_type} of {tx.quantity} {item.get_unit_display()} for '{item.name}'",
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f"Stock {tx.get_transaction_type_display()} recorded successfully!")
            return redirect('inventory:transaction_list')
    else:
        initial = {'transaction_date': timezone.now().date()}
        if request.GET.get('item'):
            initial['item'] = request.GET.get('item')
        form = StockTransactionForm(initial=initial)
    return render(request, 'inventory/transaction_form.html', {'form': form, 'page_title': 'Record Stock Transaction'})


@login_required
@accountant_required
def supplier_list_view(request):
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers, 'page_title': 'Suppliers & Vendors Directory'})


@login_required
@accountant_required
def supplier_create_view(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supp = form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Inventory', f"Added supplier '{supp.name}'", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Supplier '{supp.name}' saved!")
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'inventory/supplier_form.html', {'form': form, 'page_title': 'Add Supplier'})


@login_required
@accountant_required
def supplier_edit_view(request, pk):
    supp = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supp)
        if form.is_valid():
            supp = form.save()
            messages.success(request, f"Supplier '{supp.name}' updated!")
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supp)
    return render(request, 'inventory/supplier_form.html', {'form': form, 'supp': supp, 'page_title': f'Edit Supplier: {supp.name}'})

