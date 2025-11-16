from django.urls import path
from .views import *
from user.views import user_profile

urlpatterns = [
    path('', index, name='dashboard'),
    path('blog/', admin_blog_management, name='blog_management'),
    path('webinar/', webinar, name='webinar_management'),
    path('user/', user, name='user_management'),
    path('user/<int:pk>', user_profile, name='user_profile'),
    #path('webinar/registration/', admin_webinar_registrations, name='webinar_registration_management'),
    #path('registration/<int:pk>/', registration_detail, name='registration_detail'),
    path('registration/<int:pk>/edit/', registration_edit, name='registration_edit'),
    path('webinar/<int:pk>', webinar_reg, name='webinar_reg')
]
