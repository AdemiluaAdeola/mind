from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import *
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import *
from decimal import Decimal
from django.contrib.auth.models import User, Group
import uuid
import random

# Create your views here.
def home(request):
    # Get upcoming webinars (next 7 days)
    upcoming_webinars = Webinar.objects.filter(
        status='upcoming',
    ).order_by('start_datetime')[:6]
    
    # Get latest published blogs
    latest_blogs = Blog.objects.filter(
        status='Published',
        is_verified=True
    ).order_by('-created_at')[:6]
    
    context = {
        'upcoming_webinars': upcoming_webinars,
        'latest_blogs': latest_blogs,
    }
    
    return render(request, 'home.html', context)

def blog_list(request):
    # Get all published blogs
    blog_list = Blog.objects.filter(status='Published', is_verified=True).order_by('-created_at')
    
    # Get all categories for filter
    categories = Category.objects.filter(is_active=True)
    
    # Filter by category if specified
    category_slug = request.GET.get('category')
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        blog_list = blog_list.filter(category=category)
    
    # Pagination
    paginator = Paginator(blog_list, 9)  # Show 9 blogs per page
    page = request.GET.get('page')
    
    try:
        blogs = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        blogs = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results
        blogs = paginator.page(paginator.num_pages)
    
    context = {
        'blogs': blogs,
        'categories': categories,
        'page_obj': blogs,  # For pagination template
        'is_paginated': True,  # For pagination template
    }
    
    return render(request, 'blog_list.html', context)

def blog_detail(request, slug):
    # Get the blog post
    blog = get_object_or_404(
        Blog.objects.select_related('author', 'category').prefetch_related('tags', 'comments', 'comments__replies'),
        slug=slug, 
        status='Published', 
        is_verified=True
    )
    
    # Increment view count
    blog.views += 1
    blog.save()
    
    # Get related posts (same category or tags)
    related_blogs = Blog.objects.filter(
        Q(category=blog.category) | Q(tags__in=blog.tags.all()),
        status='Published', 
        is_verified=True
    ).exclude(id=blog.id).distinct()[:3]
    
    if request.method == 'POST':
        blog = get_object_or_404(Blog, slug=slug)
        content = request.POST.get('content')
        
        if content and request.user.is_authenticated:
            Comment.objects.create(
                blog=blog,
                user=request.user,
                content=content
            )
            # You might want to add a success message here
        
        return redirect('blog_detail', slug=slug)

    # Get all categories for footer
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'blog': blog,
        'related_blogs': related_blogs,
        'categories': categories,
    }
    
    return render(request, 'blog_detail.html', context)

#@login_required(login_url='login')
def about(request):
    return render(request, 'about.html')

def webinar_list(request):
    # Get filter parameters
    status_filter = request.GET.get('status', 'upcoming')
    topic_filter = request.GET.get('topic')
    search_query = request.GET.get('q')
    
    # Base queryset
    webinars = Webinar.objects.select_related('host').prefetch_related('speakers')
    
    # Apply status filter
    if status_filter == 'upcoming':
        webinars = webinars.filter(
            status__in=['upcoming', 'live'],
            start_datetime__gte=timezone.now()
        ).order_by('start_datetime')
    elif status_filter == 'past':
        webinars = webinars.filter(
            status='completed',
            start_datetime__lt=timezone.now()
        ).order_by('-start_datetime')
    elif status_filter == 'live':
        webinars = webinars.filter(
            status='live'
        ).order_by('start_datetime')
    else:
        webinars = webinars.all().order_by('-start_datetime')
    
    # Apply topic filter
    if topic_filter:
        webinars = webinars.filter(
            Q(title__icontains=topic_filter) |
            Q(description__icontains=topic_filter) |
            Q(speakers__name__icontains=topic_filter)
        ).distinct()
    
    # Separate upcoming and past webinars for the template
    upcoming_webinars = webinars.filter(
        start_datetime__gte=timezone.now()
    ) | webinars.filter(status='live')
    
    past_webinars = webinars.filter(
        start_datetime__lt=timezone.now(),
        status='completed'
    )
    
    context = {
        'upcoming_webinars': upcoming_webinars,
        'past_webinars': past_webinars,
        'status_filter': status_filter,
        'topic_filter': topic_filter,
    }
    
    return render(request, 'webinar_list.html', context)

def webinar_detail(request, slug):
    # Get the webinar with related data
    webinar = get_object_or_404(
        Webinar.objects.select_related('host')
                       .prefetch_related('speakers', 'resources'),
        slug=slug
    )
    
    # Check if user is registered
    user_registration = None
    if request.user.is_authenticated:
        user_registration = WebinarRegistration.objects.filter(
            webinar=webinar,
            user=request.user,
            status__in=['confirmed', 'attended']
        ).first()
    
    # Get related webinars (same category or speakers)
    related_webinars = Webinar.objects.filter(
        Q(speakers__in=webinar.speakers.all()) |
        Q(status='upcoming')
    ).exclude(id=webinar.id).distinct()[:3]
    
    context = {
        'webinar': webinar,
        'user_registration': user_registration,
        'related_webinars': related_webinars,
    }
    
    return render(request, 'webinar_detail.html', context)

def webinar_register(request, slug):
    webinar = get_object_or_404(Webinar, slug=slug)

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        questions = request.POST.get('questions', '')
        payment_proof = request.FILES.get('proof_file')

        # Generate payment reference
        payment_reference = f"MCW{webinar.id}{random.randint(1000, 9999)}"

        try:
            registration = WebinarRegistration.objects.create(
                webinar=webinar,
                full_name=full_name,
                email=email,
                questions=questions,  # match template name
                payment_reference=payment_reference,
                payment_proof=payment_proof if not webinar.is_free else None,
                status="confirmed" if webinar.is_free else "pending"
            )

            registration.save()

            messages.success(request, 'Registration submitted successfully!')
            
            # Show confirmation step instead of redirecting
            return render(request, 'webinar_registration.html', {
                'webinar': webinar,
                'payment_reference': payment_reference,
                'show_confirmation': True,
            })

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    # GET request → show form
    context = {
        'webinar': webinar,
        'payment_reference': f"MCW{webinar.id}{random.randint(1000, 9999)}",
    }
    return render(request, 'webinar_registration.html', context)
