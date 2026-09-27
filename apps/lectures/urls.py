from django.urls import path
from . import views

app_name = 'lectures'

urlpatterns = [
    path('', views.lecture_list_view, name='lecture_list'),
    path('add/', views.lecture_create_view, name='lecture_add'),
    path('homework/', views.homework_list_view, name='homework_list'),
    path('homework/add/', views.homework_create_view, name='homework_add'),
]
