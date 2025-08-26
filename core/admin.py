from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Blog)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(CommentLike)
admin.site.register(Webinar)
admin.site.register(WebinarRegistration)
admin.site.register(WebinarResource)
admin.site.register(Speaker)