from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('webinars/', views.webinar_list, name='webinar_list'),
    path('webinars/<slug:slug>/', views.webinar_detail, name='webinar_detail'),
    # path('webinars/<slug:slug>/register/', views.webinar_register, name='webinar_register'),
    # path('webinars/<slug:slug>/register/confirmation/<int:registration_id>/', views.webinar_registration_confirmation, name='webinar_registration_confirmation'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('about/', views.about, name='about'),
    # path('login/', views.login_view, name='login'),
    # path('logout/', views.logout_view, name='logout'),
    # path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    # path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/settings/', views.admin_settings, name='admin_settings'),
    path('dashboard/search/', views.admin_search, name='admin_search'),
    path('dashboard/export/', views.admin_export_data, name='admin_export'),
    path('dashboard/system-status/', views.admin_system_status, name='admin_system_status'),
    path('dashboard/activity-log/', views.admin_activity_log, name='admin_activity_log'),
        
    # User management
    path('dashboard/users/', views.admin_user_management, name='admin_user_management'),
    path('dashboard/users/create/', views.admin_user_create, name='admin_user_create'),
    path('dashboard/users/edit/<int:pk>/', views.admin_user_edit, name='admin_user_edit'),
    path('dashboard/users/delete/<int:pk>/', views.admin_user_delete, name='admin_user_delete'),
    path('dashboard`/users/<int:pk>/', views.admin_user_detail, name='admin_user_detail'),
    path('dashboard/users/<int:pk>/toggle-active/', views.admin_user_toggle_active, name='admin_user_toggle_active'),
    path('dashboard/roles/', views.admin_role_management, name='admin_role_management'),
    
    # Blog management
    path('dashboard/blogs/', views.admin_blog_management, name='admin_blog_management'),
    path('dashboard/blogs/create/', views.admin_blog_create, name='admin_blog_create'),
    path('dashboard/blogs/edit/<int:pk>/', views.admin_blog_edit, name='admin_blog_edit'),
    path('dashboard/blogs/delete/<int:pk>/', views.admin_blog_delete, name='admin_blog_delete'),
    
    # Webinar management
    path('dashboard/webinars/', views.admin_webinar_management, name='admin_webinar_management'),
    path('dashboard/webinars/create/', views.admin_webinar_create, name='admin_webinar_create'),
    path('dashboard/webinars/edit/<int:pk>/', views.admin_webinar_edit, name='admin_webinar_edit'),
    path('dashboard/webinars/delete/<int:pk>/', views.admin_webinar_delete, name='admin_webinar_delete'),
    path('dashboard/webinars/<int:pk>/', views.admin_webinar_detail, name='admin_webinar_detail'),
    path('dashboard/webinars/<int:pk>/registrations/', views.admin_webinar_registrations, name='admin_webinar_registrations'),
    path('dashboard/webinars/<int:pk>/resources/', views.admin_webinar_resources, name='admin_webinar_resources'),
    path('dashboard/speakers/', views.admin_speaker_management, name='admin_speaker_management'),
]