from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name="index"),
    path('blog/', blog.as_view(), name="blog_list"),
    path('webinar/', webinar.as_view(), name="webinar_list"),
    path('blog/<int:pk>/', blogpost, name="blogpost"),
    path('blog/create/', create.as_view(), name="create"),
    path('webinar/create/', webinar_create.as_view(), name="webinar_create"),
    path('blog/edit/<int:pk>/', update.as_view(), name="update"),
    path('webinar/edit/<int:pk>/', webinar_update.as_view(), name="webinar_update"),
    path('blog/<int:pk>/delete/', delete.as_view(), name="delete"),
    path('webinar/<int:pk>/delete/', webinar_delete.as_view(), name="webinar_delete"),
    path('webinar/<int:pk>/', webinar_detail, name="webinar_detail"),
    path('about/', about, name='about'),
    path('webinar/<int:pk>/reg', webinar_register, name='webinar_register')
]
