from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list_view, name='student_list'),
    path('add/', views.student_create_view, name='student_add'),
    path('<int:pk>/', views.student_detail_view, name='student_detail'),
    path('<int:pk>/edit/', views.student_update_view, name='student_edit'),
    path('<int:pk>/card/', views.student_card_view, name='student_card'),
    path('<int:pk>/delete/', views.student_delete_view, name='student_delete'),
    path('promotion/', views.student_promotion_view, name='student_promotion'),
]
