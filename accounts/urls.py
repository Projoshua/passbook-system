
# accounts/urls.py
from django.urls import path
from accounts import views
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='login/')),  # Redirect root to login
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-staff/', views.create_staff_view, name='create_staff'),
    path('staff-list/', views.staff_list_view, name='staff_list'),
    path('edit-staff/<int:user_id>/', views.edit_staff_view, name='edit_staff'),
    path('delete-staff/<int:user_id>/', views.delete_staff_view, name='delete_staff'),

      # Registration URLs
    path('register/student/', views.register_student, name='register_student'),
    path('register/staff/', views.register_staff, name='register_staff'),
]


