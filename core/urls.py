from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('webinars/', views.webinar_list, name='webinar_list'),
    path('webinars/<slug:slug>/', views.webinar_detail, name='webinar_detail'),
    path('webinars/<slug:slug>/register/', views.webinar_register, name='webinar_register'),
    # path('webinars/<slug:slug>/register/confirmation/<int:registration_id>/', views.webinar_registration_confirmation, name='webinar_registration_confirmation'),
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),
    path('about/', views.about, name='about'),
]