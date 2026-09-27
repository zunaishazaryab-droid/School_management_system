from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    path('', views.fee_dashboard_view, name='fee_dashboard'),
    path('invoices/', views.invoice_list_view, name='invoice_list'),
    path('invoices/bulk-generate/', views.generate_bulk_invoices_view, name='bulk_generate'),
    path('invoices/create/', views.create_single_invoice_view, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail_view, name='invoice_detail'),
    path('collect/', views.collect_payment_view, name='collect_payment'),
    path('collect/<int:invoice_id>/', views.collect_payment_view, name='collect_invoice_payment'),
    path('receipts/<int:pk>/', views.payment_receipt_view, name='payment_receipt'),
    path('ledger/<int:student_id>/', views.student_ledger_view, name='student_ledger'),
    path('defaulters/', views.fee_defaulters_view, name='defaulters_list'),
    path('structures/', views.fee_structures_view, name='fee_structures'),
    path('discounts/', views.student_discounts_view, name='student_discounts'),
]
