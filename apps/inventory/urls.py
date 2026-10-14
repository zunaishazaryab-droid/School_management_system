from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard_view, name='dashboard'),
    path('items/', views.item_list_view, name='item_list'),
    path('items/add/', views.item_create_view, name='item_create'),
    path('items/<int:pk>/edit/', views.item_edit_view, name='item_edit'),
    path('items/<int:pk>/delete/', views.item_delete_view, name='item_delete'),
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),
    path('transactions/', views.stock_transaction_list_view, name='transaction_list'),
    path('transactions/add/', views.stock_transaction_create_view, name='transaction_create'),
    path('suppliers/', views.supplier_list_view, name='supplier_list'),
    path('suppliers/add/', views.supplier_create_view, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit_view, name='supplier_edit'),
]

