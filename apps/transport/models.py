from django.db import models
from decimal import Decimal
from apps.students.models import Student


class Vehicle(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active / In Service'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'

    vehicle_number = models.CharField(max_length=50, unique=True, help_text="e.g. ICT-LEA-1234, VAN-05")
    model_name = models.CharField(max_length=100, help_text="e.g. Toyota HiAce 2024, Isuzu School Bus")
    seating_capacity = models.PositiveIntegerField(default=25)
    driver_name = models.CharField(max_length=150)
    driver_phone = models.CharField(max_length=30)
    driver_license_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['vehicle_number']
        verbose_name = 'School Vehicle / Bus'
        verbose_name_plural = 'School Vehicles & Buses'

    def __str__(self):
        return f"{self.vehicle_number} - {self.model_name} (Driver: {self.driver_name})"

    @property
    def assigned_passengers_count(self):
        return self.passenger_allocations.filter(status='ACTIVE').count()


class Route(models.Model):
    title = models.CharField(max_length=150, help_text="e.g. Route A: G-10 to Campus via F-10, F-11")
    start_point = models.CharField(max_length=150, default='Sector G-10')
    end_point = models.CharField(max_length=150, default='School Main Campus')
    monthly_fare = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('3500.00'), help_text="Standard monthly transport charge")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Transport Route'
        verbose_name_plural = 'Transport Routes'

    def __str__(self):
        return f"{self.title} (Fare: Rs. {self.monthly_fare})"


class RouteStop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    stop_name = models.CharField(max_length=150, help_text="e.g. F-10 Markaz PSO Pump")
    pickup_time = models.TimeField(help_text="e.g. 07:15 AM")
    drop_time = models.TimeField(help_text="e.g. 02:30 PM")
    stop_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['route', 'stop_order']
        verbose_name = 'Route Stop'
        verbose_name_plural = 'Route Stops'

    def __str__(self):
        return f"{self.route.title} - Stop #{self.stop_order}: {self.stop_name}"


class StudentTransportAllocation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        CANCELLED = 'CANCELLED', 'Cancelled'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='transport_allocation')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, related_name='passenger_allocations')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='allocated_students')
    stop = models.ForeignKey(RouteStop, on_delete=models.SET_NULL, null=True, blank=True)
    start_date = models.DateField()
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('3500.00'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Student Transport Allocation'
        verbose_name_plural = 'Student Transport Allocations'

    def __str__(self):
        return f"{self.student.get_full_name()} -> {self.route.title} ({self.vehicle.vehicle_number if self.vehicle else 'No Bus'})"
