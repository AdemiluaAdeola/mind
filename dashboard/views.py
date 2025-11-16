from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from core.models import *
from core.forms import *
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from decimal import Decimal
from user.models import User
import uuid
import random

# Create your views here.
def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required(login_url='login')
@user_passes_test(is_admin)
def index(response):
    context = {
        'total_users': User.objects.count(),
        'total_webinars': Webinar.objects.count(),
        'total_blogs': Blog.objects.count(),
        'published_blogs': Blog.objects.filter(is_verified=True).count(),
    }
    return render(response, 'dashboard/admin_dashboard.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_blog_management(response):
    blogs = Blog.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    authors = User.objects.filter(blog__isnull=False).distinct()
    
    context = {
        'blogs': blogs,
        'categories': categories,
        'authors': authors,
    }
    return render(response, 'dashboard/admin_blog_management.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def webinar(response):
    webinars = Webinar.objects.all().order_by('-start_datetime')
    hosts = User.objects.filter(hosted_webinars__isnull=False).distinct()
    
    context = {
        'webinars': webinars,
        'hosts': hosts,
    }
    return render(response, 'dashboard/webinar_management.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def user(response):
    users = User.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
    }
    return render(response, 'dashboard/user_management.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def admin_webinar_registrations(response, webinar_id=None):
    if webinar_id:
        webinar = get_object_or_404(Webinar, id=webinar_id)
        registrations = WebinarRegistration.objects.filter(webinar=webinar)
    else:
        webinar = None
        registrations = WebinarRegistration.objects.all()
    
    webinars = Webinar.objects.all()
    
    context = {
        'registrations': registrations,
        'webinars': webinars,
        'webinar': webinar,
    }
    return render(response, 'dashboard/admin_webinar_registrations.html', context)

@login_required(login_url='login')
@user_passes_test(is_admin)
def registration_edit(response, pk):
    """Edit a registration"""
    registration = get_object_or_404(WebinarRegistration, pk=pk)
    
    if response.method == 'POST':
        form = RegistrationForm(response.POST, instance=registration)
        if form.is_valid():
            form.save()
            messages.success(response, 'Registration updated successfully!')
            return redirect('webinar_management')
    else:
        form = RegistrationForm(instance=registration)
    
    return render(response, 'dashboard/registrations.html', {
        'form': form,
        'registration': registration
    })

@login_required(login_url='login')
@user_passes_test(is_admin)
def webinar_reg(response, pk):
    webinar = get_object_or_404(Webinar, id=pk)
    registrations = WebinarRegistration.objects.filter(webinar=webinar)

    return render(response, 'dashboard/webinar_details.html', {'webinar':webinar, 'registrations':registrations})