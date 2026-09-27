from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.teacher_list_view, name='teacher_list'),
    path('add/', views.teacher_create_view, name='teacher_add'),
    path('<int:pk>/', views.teacher_detail_view, name='teacher_detail'),
    path('<int:pk>/edit/', views.teacher_update_view, name='teacher_edit'),
    path('salaries/', views.salary_list_view, name='salary_list'),
]
