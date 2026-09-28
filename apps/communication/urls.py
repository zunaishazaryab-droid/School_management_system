from django.urls import path
from . import views

app_name = 'communication'

urlpatterns = [
    path('', views.announcement_list_view, name='announcement_list'),
    path('announcements/create/', views.announcement_create_view, name='announcement_create'),
    path('announcements/<int:pk>/', views.announcement_detail_view, name='announcement_detail'),
    path('announcements/<int:pk>/edit/', views.announcement_edit_view, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete_view, name='announcement_delete'),
    
    path('broadcast/', views.broadcast_center_view, name='broadcast_center'),
    path('templates/', views.template_list_view, name='template_list'),
    path('templates/<int:pk>/delete/', views.template_delete_view, name='template_delete'),
    path('history/', views.communication_history_view, name='history'),
]
