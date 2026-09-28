from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count

from apps.accounts.decorators import coordinator_required
from apps.core.models import ActivityLog
from .models import Vehicle, Route, RouteStop, StudentTransportAllocation
from .forms import VehicleForm, RouteForm, AllocationForm


@login_required
def transport_dashboard_view(request):
    """Transport Fleet & Route Overview"""
    vehicles = Vehicle.objects.all()
    routes = Route.objects.prefetch_related('stops', 'allocated_students').all()
    allocations = StudentTransportAllocation.objects.filter(status='ACTIVE').select_related('student', 'vehicle', 'route')

    total_capacity = sum(v.seating_capacity for v in vehicles)
    total_passengers = allocations.count()
    monthly_revenue = allocations.aggregate(total=Sum('monthly_fee'))['total'] or 0

    return render(request, 'transport/transport_dashboard.html', {
        'vehicles': vehicles,
        'routes': routes,
        'allocations': allocations[:8],
        'total_capacity': total_capacity,
        'total_passengers': total_passengers,
        'monthly_revenue': monthly_revenue,
        'page_title': 'School Transport & Fleet Management'
    })


@login_required
@coordinator_required
def vehicle_list_view(request):
    vehicles = Vehicle.objects.all()
    return render(request, 'transport/vehicle_list.html', {
        'vehicles': vehicles,
        'page_title': 'Vehicles & Bus Fleet Directory'
    })


@login_required
@coordinator_required
def vehicle_create_view(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            v = form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Transport', f"Added vehicle {v.vehicle_number} ({v.model_name})", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Vehicle '{v.vehicle_number}' added successfully!")
            return redirect('transport:vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'transport/vehicle_form.html', {'form': form, 'page_title': 'Add New Vehicle'})


@login_required
@coordinator_required
def route_list_view(request):
    routes = Route.objects.prefetch_related('stops', 'allocated_students').all()
    return render(request, 'transport/route_list.html', {
        'routes': routes,
        'page_title': 'Transport Routes & Stops'
    })


@login_required
@coordinator_required
def route_create_view(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            r = form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Transport', f"Added transport route: {r.title}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Route '{r.title}' created!")
            return redirect('transport:route_list')
    else:
        form = RouteForm()
    return render(request, 'transport/route_form.html', {'form': form, 'page_title': 'Create Transport Route'})


@login_required
@coordinator_required
def allocation_list_view(request):
    allocations = StudentTransportAllocation.objects.select_related('student', 'vehicle', 'route', 'stop').all()
    return render(request, 'transport/allocation_list.html', {
        'allocations': allocations,
        'page_title': 'Student Transport Allocations'
    })


@login_required
@coordinator_required
def allocation_create_view(request):
    if request.method == 'POST':
        form = AllocationForm(request.POST)
        if form.is_valid():
            alloc = form.save()
            ActivityLog.log_activity(request.user, 'CREATE', 'Transport', f"Allocated transport for student {alloc.student.get_full_name()} on route {alloc.route.title}", request.META.get('REMOTE_ADDR'))
            messages.success(request, f"Transport assigned for {alloc.student.get_full_name()}!")
            return redirect('transport:allocation_list')
    else:
        form = AllocationForm()
    return render(request, 'transport/allocation_form.html', {'form': form, 'page_title': 'Allocate Transport to Student'})
