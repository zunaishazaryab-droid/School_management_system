from django.urls import path
from . import views

app_name = 'lectures'

urlpatterns = [
    path('', views.lecture_list_view, name='lecture_list'),
    path('add/', views.lecture_create_view, name='lecture_add'),
    path('<int:pk>/', views.lecture_detail_view, name='lecture_detail'),
    path('<int:pk>/edit/', views.lecture_edit_view, name='lecture_edit'),
    path('<int:pk>/delete/', views.lecture_delete_view, name='lecture_delete'),
    
    # Homework & Diary
    path('homework/', views.homework_list_view, name='homework_list'),
    path('homework/add/', views.homework_create_view, name='homework_add'),
    path('homework/<int:pk>/', views.homework_detail_view, name='homework_detail'),
    path('homework/<int:homework_id>/submit/', views.submit_homework_action, name='submit_homework'),
    path('homework/evaluate/<int:submission_id>/', views.evaluate_submission_action, name='evaluate_submission'),
]
