from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    path('classes/', views.class_list_view, name='class_list'),
    path('classes/<int:pk>/delete/', views.class_delete_view, name='class_delete'),
    path('subjects/', views.subject_list_view, name='subject_list'),
    path('api/sections/<int:class_id>/', views.api_get_sections, name='api_sections'),
]
