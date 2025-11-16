from django.shortcuts import render, redirect
from django.contrib.auth.models import auth
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import *
from django.views.generic import ListView, DetailView
from .forms import UserForm, UserProfileForm
from core.models import WebinarRegistration

# Create your views here.
def register(response):

    if response.method == 'POST':
        username = response.POST['username']
        first_name = response.POST['first_name']
        last_name = response.POST['last_name']
        email = response.POST['email']
        password = response.POST['password']
        password2 = response.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(response, 'Email Taken')
                return redirect('register')
            
            else:
                user = User.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
                user.save()

                #log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(response, user_login)

                #create a Profile object for the new user
                return redirect(edit_profile)
        else:
            messages.info(response, 'Password Does Not Match')
            return redirect('register')
        
    else:
        return render(response, 'registration/register.html')

def staff_register(response):

    if response.method == 'POST':
        username = response.POST['username']
        first_name = response.POST['first_name']
        last_name = response.POST['last_name']
        email = response.POST['email']
        password = response.POST['password1']
        password2 = response.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(response, 'Email Taken')
                return redirect('register')
            
            else:
                user = User.objects.create_user(
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    email=email,
                    is_staff=True,
                    is_superuser = True,
                    password=password,
                )
                user.save()

                #log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(response, user_login)

                #create a Profile object for the new user
                return redirect('dashboard')
        else:
            messages.info(response, 'Password Does Not Match')
            return redirect('staff_register')
        
    else:
        return render(response, 'registration/staff_reg.html')

def login(response):
    if response.method == 'POST':
        username = response.POST['username']
        password = response.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(response, user)
            if user.is_staff == True:
                return redirect('dashboard')
            else:
                return redirect('/')
        else:
            messages.info(response, 'Credentials Invalid')
            return redirect('login')
    
    return render(response, 'registration/login.html')

@login_required(login_url='login')
def logout(response):
    auth.logout(response)
    return redirect('login')

@login_required(login_url='login')
def profile(response):
    user = response.user
    # Get user's registered webinars
    registered_webinars = WebinarRegistration.objects.filter(email=user.email).select_related('webinar')
    
    context = {
        'user': user,
        #'countries': countries,
        'registered_webinars': registered_webinars,
    }
    return render(response, 'user/profile.html', context)

@login_required(login_url='login')
def edit_profile(response):
    if response.method == 'POST':
        user_form = UserProfileForm(response.POST, instance=response.user)
        
        if user_form.is_valid():
            user_form.save()
            messages.success(response, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=response.user)

    context = {
        'user_form': user_form,
    }
    return render(response, 'user/edit_profile.html', context)

class UserListView(ListView):
    model = User
    template_name = 'user/user_list.html'
    ordering = ['-date_joined']

def user_profile(response, pk):
    user = User.objects.get(id=pk)
    
    context = {
        'user': user,
    }
    return render(response, 'user/profile.html', context)