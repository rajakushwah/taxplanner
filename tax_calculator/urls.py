"""
URL Configuration for Tax Calculator App
"""
from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # User Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    
    # Tax Calculation
    path('calculate/', views.calculate_tax, name='calculate_tax'),
    path('result/<uuid:pk>/', views.tax_result, name='tax_result'),
    path('edit/<uuid:pk>/', views.edit_salary, name='edit_salary'),
    path('delete/<uuid:pk>/', views.delete_salary, name='delete_salary'),
    
    # API
    path('api/quick-calculate/', views.quick_calculate, name='quick_calculate'),
    
    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/user/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-panel/calculation/<uuid:pk>/', views.admin_view_calculation, name='admin_view_calculation'),
]
