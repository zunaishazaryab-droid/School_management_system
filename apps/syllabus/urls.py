from django.urls import path
from . import views

app_name = 'syllabus'

urlpatterns = [
    path('', views.syllabus_tracker_view, name='tracker'),
    path('chapter/add/', views.chapter_create_view, name='chapter_add'),
    path('topic/add/', views.topic_create_view, name='topic_add'),
]
