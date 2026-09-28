from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard_view, name='dashboard'),
    path('items/', views.item_list_view, name='item_list'),
    path('items/add/', views.item_create_view, name='item_create'),
    path('transactions/', views.stock_transaction_list_view, name='transaction_list'),
    path('transactions/add/', views.stock_transaction_create_view, name='transaction_create'),
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/add/', views.supplier_create_view, name='supplier_create'),
]
