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

# Create your views here.
def home(request):
    # Get upcoming webinars (next 7 days)
    upcoming_webinars = Webinar.objects.filter(
        status='upcoming',
        start_datetime__gte=timezone.now(),
        start_datetime__lte=timezone.now() + timezone.timedelta(days=7)
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
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        blog_list = blog_list.filter(
            Q(title__icontains=query) | 
            Q(excerpt__icontains=query) | 
            Q(content__icontains=query) |
            Q(category__name__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
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
        Blog.objects.select_related('author', 'category')
                   .prefetch_related('tags', 'comments', 'comments__replies'),
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
    
    # Get all categories for footer
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'blog': blog,
        'related_blogs': related_blogs,
        'categories': categories,
    }
    
    return render(request, 'blog_detail.html', context)

def blog_comment(request, slug):
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
    
    return redirect('blog_detail', slug=slug)

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
    
    # Apply search query
    if search_query:
        webinars = webinars.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(speakers__name__icontains=search_query)
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
        'search_query': search_query,
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

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_blog_management(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    
    # Start with all blogs
    blogs = Blog.objects.all().select_related('author', 'category').prefetch_related('tags')
    
    # Apply filters
    if status_filter:
        blogs = blogs.filter(status=status_filter)
    
    if category_filter:
        blogs = blogs.filter(category__slug=category_filter)
    
    if search_query:
        blogs = blogs.filter(
            Q(title__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query)
        )
    
    # Get statistics
    total_posts = Blog.objects.count()
    published_posts = Blog.objects.filter(status='Published').count()
    draft_posts = Blog.objects.filter(status='Draft').count()
    total_views = Blog.objects.aggregate(total_views=models.Sum('views'))['total_views'] or 0
    
    # Pagination
    paginator = Paginator(blogs, 10)  # Show 10 blogs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'blogs': page_obj,
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_views': total_views,
        'categories': categories,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'search_query': search_query,
    }
    
    return render(request, 'blog_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_blog_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save(commit=False)  # Don't save yet
            blog.author = request.user
            
            # Handle status based on which button was clicked
            if 'publish' in request.POST:
                blog.status = 'Published'
                message = 'Blog post published successfully!'
            else:
                blog.status = 'Draft'
                message = 'Blog post saved as draft!'
            
            blog.save()
            form.save_m2m()  # Save many-to-many data (tags)
            
            messages.success(request, message)
            return redirect('admin_blog_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BlogForm()
    
    context = {
        'form': form,
        'title': 'Create New Blog Post',
    }
    return render(request, 'blog_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_blog_edit(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            blog = form.save()
            
            # Handle status based on which button was clicked
            if 'publish' in request.POST:
                blog.status = 'Published'
                message = 'Blog post published successfully!'
            elif 'save_draft' in request.POST:
                blog.status = 'Draft'
                message = 'Blog post saved as draft!'
            
            blog.save()
            messages.success(request, message)
            return redirect('admin_blog_management')
    else:
        form = BlogForm(instance=blog)
    
    context = {
        'form': form,
        'blog': blog,
        'title': 'Edit Blog Post',
    }
    return render(request, 'blog_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_blog_delete(request, pk):
    blog = get_object_or_404(Blog, pk=pk)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.delete()
        messages.success(request, f'Blog post "{blog_title}" deleted successfully!')
        return redirect('admin_blog_management')
    
    context = {
        'blog': blog,
    }
    return render(request, 'blog_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_category_management(request):
    categories = Category.objects.annotate(
        post_count=Count('blogs')
    ).order_by('order', 'name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'blog_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_management(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    # Start with all webinars
    webinars = Webinar.objects.all().select_related('host').prefetch_related('speakers')
    
    # Apply filters
    if status_filter:
        webinars = webinars.filter(status=status_filter)
    
    if search_query:
        webinars = webinars.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(host__username__icontains=search_query) |
            Q(host__first_name__icontains=search_query) |
            Q(host__last_name__icontains=search_query) |
            Q(speakers__name__icontains=search_query)
        ).distinct()
    
    # Get statistics
    total_webinars = Webinar.objects.count()
    upcoming_webinars = Webinar.objects.filter(
        status='upcoming', 
        start_datetime__gt=timezone.now()
    ).count()
    live_webinars = Webinar.objects.filter(status='live').count()
    completed_webinars = Webinar.objects.filter(status='completed').count()
    
    # Calculate total revenue (for paid webinars)
    total_revenue = WebinarRegistration.objects.filter(
        status='confirmed',
        webinar__price__gt=0
    ).aggregate(total=Sum('webinar__price'))['total'] or 0
    
    # Pagination
    paginator = Paginator(webinars, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'webinars': page_obj,
        'total_webinars': total_webinars,
        'upcoming_webinars': upcoming_webinars,
        'live_webinars': live_webinars,
        'completed_webinars': completed_webinars,
        'total_revenue': total_revenue,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'webinar_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_create(request):
    if request.method == 'POST':
        form = WebinarForm(request.POST, request.FILES)
        if form.is_valid():
            webinar = form.save(commit=False)
            webinar.host = request.user
            
            # Check if webinar should be live based on start time
            if webinar.start_datetime <= timezone.now():
                webinar.status = 'live'
            
            webinar.save()
            form.save_m2m()  # Save many-to-many data (speakers)
            
            messages.success(request, 'Webinar created successfully!')
            return redirect('admin_webinar_management')
    else:
        form = WebinarForm()
    
    context = {
        'form': form,
        'title': 'Create New Webinar',
    }
    return render(request, 'webinar_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_edit(request, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    
    if request.method == 'POST':
        form = WebinarForm(request.POST, request.FILES, instance=webinar)
        if form.is_valid():
            webinar = form.save()
            
            # Update status based on time
            if webinar.start_datetime <= timezone.now() and webinar.status == 'upcoming':
                webinar.status = 'live'
                webinar.save()
            
            messages.success(request, 'Webinar updated successfully!')
            return redirect('admin_webinar_management')
    else:
        form = WebinarForm(instance=webinar)
    
    context = {
        'form': form,
        'webinar': webinar,
        'title': 'Edit Webinar',
    }
    return render(request, 'webinar_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_detail(request, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    registrations = webinar.registrations.select_related('user').all()
    resources = webinar.resources.all()
    speakers = webinar.speakers.all()
    
    # Registration statistics
    confirmed_registrations = registrations.filter(status='confirmed').count()
    attended_registrations = registrations.filter(attendance_confirmed=True).count()
    
    context = {
        'webinar': webinar,
        'registrations': registrations,
        'resources': resources,
        'speakers': speakers,
        'confirmed_registrations': confirmed_registrations,
        'attended_registrations': attended_registrations,
        'seats_remaining': webinar.seats_remaining,
    }
    
    return render(request, 'webinar_info.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_delete(request, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    
    if request.method == 'POST':
        webinar_title = webinar.title
        webinar.delete()
        messages.success(request, f'Webinar "{webinar_title}" deleted successfully!')
        return redirect('admin_webinar_management')
    
    context = {
        'webinar': webinar,
    }
    return render(request, 'webinar_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_speaker_management(request):
    speakers = Speaker.objects.annotate(
        webinar_count=Count('webinars')
    ).order_by('name')
    
    if request.method == 'POST':
        form = SpeakerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Speaker added successfully!')
            return redirect('admin_speaker_management')
    else:
        form = SpeakerForm()
    
    context = {
        'speakers': speakers,
        'form': form,
    }
    return render(request, 'speaker_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_registrations(request, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    registrations = webinar.registrations.select_related('user').all()
    
    # Export functionality
    export_format = request.GET.get('export')
    if export_format == 'csv':
        # Implement CSV export here
        pass
    
    context = {
        'webinar': webinar,
        'registrations': registrations,
    }
    return render(request, 'webinar_registrations.html', context)

@login_required
@user_passes_test(is_admin)
def admin_webinar_resources(request, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    
    if request.method == 'POST':
        form = WebinarResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.webinar = webinar
            resource.save()
            messages.success(request, 'Resource added successfully!')
            return redirect('admin_webinar_resources', pk=pk)
    else:
        form = WebinarResourceForm()
    
    resources = webinar.resources.all()
    
    context = {
        'webinar': webinar,
        'resources': resources,
        'form': form,
    }
    return render(request, 'webinar_resources.html', context)

@login_required
@user_passes_test(is_admin)
def update_webinar_status(request, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Webinar.STATUS_CHOICES):
            webinar.status = new_status
            webinar.save()
            messages.success(request, f'Webinar status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('admin_webinar_detail', pk=pk)

@login_required
@user_passes_test(is_admin)
def admin_user_management(request):
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('q', '')
    
    # Start with all users
    users = User.objects.all().select_related('profile').prefetch_related('groups')
    
    # Apply filters
    if role_filter:
        users = users.filter(groups__name=role_filter)
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(profile__country__icontains=search_query)
        ).distinct()
    
    # Get statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # Get available roles/groups
    roles = Group.objects.annotate(user_count=Count('user'))
    
    # Pagination
    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'roles': roles,
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'user_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_create(request):
    if request.method == 'POST':
        user_form = UserCreationFormExtended(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save user
            user = user_form.save(commit=False)
            user.is_active = True
            user.save()
            
            # Save profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Save groups
            user_form.save_m2m()
            
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('admin_user_management')
    else:
        user_form = UserCreationFormExtended()
        profile_form = ProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': 'Create New User',
    }
    return render(request, 'admin_user_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_object_or_404(Profile, user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save()
            
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('admin_user_management')
    else:
        user_form = UserForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
        'title': f'Edit User: {user.username}',
    }
    return render(request, 'admin_user_form.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_object_or_404(Profile, user=user)
    
    # Get user activity statistics
    blog_count = user.blogs.count()
    webinar_registrations = user.webinar_registrations.count()
    comments_count = user.comments.count()
    
    context = {
        'user': user,
        'profile': profile,
        'blog_count': blog_count,
        'webinar_registrations': webinar_registrations,
        'comments_count': comments_count,
    }
    
    return render(request, 'user_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        action = "activated" if user.is_active else "deactivated"
        messages.success(request, f'User {user.username} has been {action}.')
    
    return redirect('admin_user_management')

@login_required
@user_passes_test(is_admin)
def admin_user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        if user == request.user:
            messages.error(request, 'You cannot delete your own account!')
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} deleted successfully!')
        return redirect('admin_user_management')
    
    context = {
        'user': user,
    }
    return render(request, 'user_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def admin_user_impersonate(request, pk):
    user = get_object_or_404(User, pk=pk)
    
    # Store original user ID in session
    request.session['original_user'] = request.user.id
    request.session['impersonating'] = True
    
    # Log in as the target user
    from django.contrib.auth import login
    login(request, user)
    
    messages.info(request, f'Now impersonating {user.username}')
    return redirect('home')

@login_required
def admin_stop_impersonate(request):
    if 'original_user' in request.session:
        original_user_id = request.session.get('original_user')
        original_user = get_object_or_404(User, pk=original_user_id)
        
        # Log back in as original user
        from django.contrib.auth import login
        login(request, original_user)
        
        # Clear session variables
        del request.session['original_user']
        del request.session['impersonating']
        
        messages.info(request, 'Stopped impersonating')
    
    return redirect('admin_user_management')

@login_required
@user_passes_test(is_admin)
def admin_user_export(request):
    # Simple export functionality - can be extended to CSV/Excel
    users = User.objects.all().select_related('profile')
    
    # This would typically generate a CSV or Excel file
    # For now, we'll just show a message
    messages.info(request, 'User export functionality would generate a CSV file here.')
    return redirect('admin_user_management')

@login_required
@user_passes_test(is_admin)
def admin_role_management(request):
    if request.method == 'POST':
        role_name = request.POST.get('role_name')
        if role_name:
            Group.objects.get_or_create(name=role_name)
            messages.success(request, f'Role "{role_name}" created successfully!')
    
    roles = Group.objects.annotate(user_count=Count('user'))
    
    context = {
        'roles': roles,
    }
    return render(request, 'role_management.html', context)

@login_required
@user_passes_test(is_admin)
def admin_assign_role(request, user_id, role_id):
    user = get_object_or_404(User, pk=user_id)
    role = get_object_or_404(Group, pk=role_id)
    
    user.groups.add(role)
    messages.success(request, f'Role "{role.name}" assigned to {user.username}')
    
    return redirect('admin_user_edit', pk=user_id)

@login_required
@user_passes_test(is_admin)
def admin_remove_role(request, user_id, role_id):
    user = get_object_or_404(User, pk=user_id)
    role = get_object_or_404(Group, pk=role_id)
    
    user.groups.remove(role)
    messages.success(request, f'Role "{role.name}" removed from {user.username}')
    
    return redirect('admin_user_edit', pk=user_id)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard with statistics and recent activity"""
    
    # Calculate statistics
    total_users = User.objects.count()
    total_blogs = Blog.objects.count()
    total_webinars = Webinar.objects.count()
    total_views = Blog.objects.aggregate(total_views=Sum('views'))['total_views'] or 0
    
    # Get recent activity
    upcoming_webinars = Webinar.objects.filter(
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')[:5]
    
    recent_blogs = Blog.objects.order_by('-created_at')[:5]
    
    # Calculate storage usage (placeholder - would need actual implementation)
    used_storage = 1024  # MB
    total_storage = 5120  # MB
    
    # Get last backup time (placeholder)
    last_backup = timezone.now() - timedelta(hours=12)
    
    context = {
        'title': 'Dashboard',
        'total_users': total_users,
        'total_blogs': total_blogs,
        'total_webinars': total_webinars,
        'total_views': total_views,
        'upcoming_webinars': upcoming_webinars,
        'recent_blogs': recent_blogs,
        'used_storage': used_storage,
        'total_storage': total_storage,
        'last_backup': last_backup,
    }
    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_settings(request):
    """Admin settings page"""
    
    if request.method == 'POST':
        # Handle settings form submission
        # This would typically save settings to database or configuration file
        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_settings')
    
    # Default settings (would typically come from database)
    default_settings = {
        'site_name': 'MindCraft ThinkSpace',
        'site_description': 'Platform for mindset transformation and innovation',
        'admin_email': 'admin@mindcraft.com',
        'items_per_page': 20,
        'auto_backup': True,
        'backup_frequency': 'daily',
        'email_notifications': True,
    }
    
    context = {
        'title': 'Settings',
        'settings': default_settings,
    }
    
    return render(request, 'admin_settings.html', context)

@login_required
@user_passes_test(is_admin)
def admin_search(request):
    """Global search functionality across all models"""
    
    query = request.GET.get('q', '').strip()
    results = {
        'users': [],
        'blogs': [],
        'webinars': [],
    }
    
    if query:
        # Search users
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).select_related('profile')[:10]
        
        # Search blogs
        blogs = Blog.objects.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(content__icontains=query)
        ).select_related('author', 'category')[:10]
        
        # Search webinars
        webinars = Webinar.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        ).select_related('host')[:10]
        
        results = {
            'users': users,
            'blogs': blogs,
            'webinars': webinars,
        }
    
    # Calculate result counts
    total_results = (
        len(results['users']) + 
        len(results['blogs']) + 
        len(results['webinars'])
    )
    
    context = {
        'title': 'Search Results',
        'query': query,
        'results': results,
        'total_results': total_results,
        'user_count': len(results['users']),
        'blog_count': len(results['blogs']),
        'webinar_count': len(results['webinars']),
    }
    
    return render(request, 'admin_search.html', context)

@login_required
@user_passes_test(is_admin)
def admin_export_data(request):
    """Export data functionality"""
    
    export_type = request.GET.get('type', '')
    format_type = request.GET.get('format', 'csv')
    
    if export_type == 'users':
        return export_users(request, format_type)
    elif export_type == 'blogs':
        return export_blogs(request, format_type)
    elif export_type == 'webinars':
        return export_webinars(request, format_type)
    elif export_type == 'registrations':
        webinar_id = request.GET.get('webinar_id')
        return export_registrations(request, webinar_id, format_type)
    
    messages.error(request, 'Invalid export type')
    return redirect('admin_dashboard')

def export_users(request, format_type='csv'):
    """Export users data"""
    # Implementation would generate CSV/Excel file
    # Placeholder implementation
    messages.info(request, 'User export functionality would generate a file here.')
    return redirect('admin_user_management')

def export_blogs(request, format_type='csv'):
    """Export blogs data"""
    messages.info(request, 'Blog export functionality would generate a file here.')
    return redirect('admin_blog_management')

def export_webinars(request, format_type='csv'):
    """Export webinars data"""
    messages.info(request, 'Webinar export functionality would generate a file here.')
    return redirect('admin_webinar_management')

def export_registrations(request, webinar_id, format_type='csv'):
    """Export webinar registrations"""
    messages.info(request, 'Registration export functionality would generate a file here.')
    return redirect('admin_webinar_detail', pk=webinar_id)

@login_required
@user_passes_test(is_admin)
def admin_system_status(request):
    """System status and health check"""
    
    # Placeholder system status data
    system_status = {
        'database': {
            'status': 'online',
            'size': '2.5 GB',
            'tables': 24,
        },
        'storage': {
            'used': '1.2 GB',
            'total': '5 GB',
            'percent_used': 24,
        },
        'performance': {
            'response_time': '120ms',
            'uptime': '99.8%',
            'load_average': '0.8',
        },
        'backups': {
            'last_backup': timezone.now() - timedelta(hours=6),
            'backup_size': '450 MB',
            'auto_backup': True,
        }
    }
    
    context = {
        'title': 'System Status',
        'system_status': system_status,
    }
    
    return render(request, 'admin_system_status.html', context)

@login_required
@user_passes_test(is_admin)
def admin_activity_log(request):
    """Admin activity log viewer"""
    
    # Placeholder activity data
    activities = [
        {
            'user': request.user,
            'action': 'Login',
            'timestamp': timezone.now() - timedelta(minutes=5),
            'details': 'User logged into admin panel',
        },
        {
            'user': request.user,
            'action': 'Create',
            'timestamp': timezone.now() - timedelta(hours=1),
            'details': 'Created new blog post',
        },
        {
            'user': request.user,
            'action': 'Update',
            'timestamp': timezone.now() - timedelta(hours=2),
            'details': 'Updated user permissions',
        },
    ]
    
    context = {
        'title': 'Activity Log',
        'activities': activities,
    }
    
    return render(request, 'admin_activity_log.html', context)