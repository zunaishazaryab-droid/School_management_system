from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    path('', views.expense_list_view, name='expense_list'),
    path('add/', views.expense_create_view, name='expense_create'),
    path('<int:pk>/edit/', views.expense_update_view, name='expense_update'),
    path('<int:pk>/delete/', views.expense_delete_view, name='expense_delete'),
    path('summary/', views.financial_summary_view, name='financial_summary'),
    path('categories/', views.expense_categories_view, name='category_list'),
]
