from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login, name='login'),
    path('signup/', register, name='register'),
    path('logout/', logout, name='logout'),
    path('profile/', profile_view, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
]
