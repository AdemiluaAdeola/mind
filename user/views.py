# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import ProfileForm, UserForm
from core.models import Webinar, WebinarRegistration

# Create your views here.
def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email already taken')
                return redirect('register')
            else:
                # Set username = email so authentication works
                user = User.objects.create_user(
                    username=email,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    password=password
                )
                user.save()

                # Log user in right after registration
                user_login = auth.authenticate(username=email, password=password)
                auth.login(request, user_login)

                # Create profile object for the new user
                user_model = User.objects.get(email=email)
                new_profile = Profile.objects.create(user=user_model)
                new_profile.save()

                return redirect('edit_profile')
        else:
            messages.info(request, 'Passwords do not match')
            return redirect('register')

    else:
        return render(request, 'register.html')

def login(request):
    if request.method == 'POST':
        email = request.POST['email']   # field name is still 'username' in your form
        password = request.POST['password']

        try:
            # Get the user object based on email
            user_obj = User.objects.get(email=email)
            # Authenticate using the username behind the scenes
            user = auth.authenticate(email=email, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Invalid username or password')
            return redirect('login')

    return render(request, 'login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    return redirect('login')

@login_required(login_url='login')
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    # Get registered webinars
    registered_webinars = WebinarRegistration.objects.filter(
        email=request.user.email
    ).select_related('webinar')
    
    # Get attended webinars (if you implement attendance tracking)
    attended_webinars = Webinar.objects.filter(
        registrations__email=request.user.email,
        registrations__attendance_confirmed=True
    )
    
    context = {
        'profile': profile,
        'registered_webinars': registered_webinars,
        'attended_webinars': attended_webinars,
    }
    
    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        # Handle both user and profile forms
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
        else:
            # If forms are invalid, show error messages
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"User {field}: {error}")
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"Profile {field}: {error}")
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    }
    
    return render(request, 'edit_profile.html', context)