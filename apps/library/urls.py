from django.urls import path
from . import views

app_name = 'library'

urlpatterns = [
    path('', views.library_dashboard_view, name='dashboard'),
    path('books/', views.book_list_view, name='book_list'),
    path('books/add/', views.book_create_view, name='book_create'),
    path('issues/', views.book_issue_list_view, name='issue_list'),
    path('issues/add/', views.book_issue_create_view, name='issue_create'),
    path('issues/<int:pk>/return/', views.book_return_view, name='book_return'),
]
