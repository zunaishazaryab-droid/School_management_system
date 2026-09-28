from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    path('', views.transport_dashboard_view, name='dashboard'),
    path('vehicles/', views.vehicle_list_view, name='vehicle_list'),
    path('vehicles/add/', views.vehicle_create_view, name='vehicle_add'),
    path('routes/', views.route_list_view, name='route_list'),
    path('routes/add/', views.route_create_view, name='route_add'),
    path('allocations/', views.allocation_list_view, name='allocation_list'),
    path('allocations/add/', views.allocation_create_view, name='allocation_add'),
]
