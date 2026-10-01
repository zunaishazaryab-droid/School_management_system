from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list_view, name='student_list'),
    path('dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('<int:pk>/dashboard/', views.student_dashboard_view, name='student_specific_dashboard'),
    path('add/', views.student_create_view, name='student_add'),
    path('portal/', views.parent_portal_view, name='parent_portal'),
    path('batch-id-cards/', views.student_batch_id_cards_view, name='batch_id_cards'),
    path('<int:pk>/', views.student_detail_view, name='student_detail'),
    path('<int:pk>/edit/', views.student_update_view, name='student_edit'),
    path('<int:pk>/card/', views.student_card_view, name='student_card'),
    path('<int:pk>/id-card/', views.student_card_view, name='student_id_card_alias'),
    path('<int:pk>/certificate/', views.student_certificate_view, name='student_certificate'),
    path('<int:pk>/delete/', views.student_delete_view, name='student_delete'),
    path('promotion/', views.student_promotion_view, name='student_promotion'),
]

