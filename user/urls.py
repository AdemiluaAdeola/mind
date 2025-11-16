from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('profile/', profile, name="profile"),
    path('profile/update/', edit_profile, name='update_profile'),
    path('list/', UserListView.as_view()),
    path('register/staff', staff_register, name='staff_register')
]
