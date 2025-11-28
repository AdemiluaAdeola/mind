from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from .forms import CreateNewPost, UpdatePost, CommentSection, CreateWebinar, WebinarRegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

# Create your views here.

@login_required(login_url='login')
def index(response):
    posts = Blog.objects.filter(is_verified=True).order_by('-created_at')[:3]
    webinars=Webinar.objects.all().order_by('-created_at')[:3]

    context = {
        'posts':posts,
        'webinars':webinars
    }

    return render(response, 'core/index.html', context)

@method_decorator(login_required(login_url='login'), name='dispatch')
class blog(ListView):
    model = Blog
    template_name = 'blog/index.html'
    ordering = ['-created_at']
    paginate_by = 10

@method_decorator(login_required(login_url='login'), name='dispatch')
class webinar(ListView):
    model = Webinar
    template_name = 'webinar/index.html'
    ordering = ['-created_at']
    paginate_by = 10
    
@method_decorator(login_required(login_url='login'), name='dispatch')
class create(CreateView):
    model = Blog
    template_name = 'blog/create.html'
    form_class = CreateNewPost

@method_decorator(login_required(login_url='login'), name='dispatch')
class webinar_create(CreateView):
    model = Webinar
    template_name = 'webinar/create.html'
    form_class = CreateWebinar

@method_decorator(login_required(login_url='login'), name='dispatch')
class update(UpdateView):
    model = Blog
    template_name = 'blog/update.html'
    form_class = UpdatePost

@method_decorator(login_required(login_url='login'), name='dispatch')
class webinar_update(UpdateView):
    model = Webinar
    template_name = 'webinar/create.html'
    form_class = CreateWebinar

@method_decorator(login_required(login_url='login'), name='dispatch')
class delete(DeleteView):
    model = Blog
    template_name = 'blog/delete.html'
    success_url = reverse_lazy('index')

@method_decorator(login_required(login_url='login'), name='dispatch')
class webinar_delete(DeleteView):
    model = Blog
    template_name = 'blog/delete.html'
    success_url = reverse_lazy('webinar')

@login_required(login_url='login')
def blogpost(response, pk):
    blog = Blog.objects.get(id=pk)
    if response.method == "POST":
        form = CommentSection(response.POST)
        if form.is_valid():
            n = f"{response.user.first_name} {response.user.last_name}"
            c = form.cleaned_data["body"]
            Comment.objects.create(
                blog=blog,
                name=n,
                body=c
            )
            return redirect('blogpost', pk=pk)

    else:
        form = CommentSection()
        return render(response, 'blog/post.html', {'blog':blog, 'form':form})

@login_required(login_url='login')
def about(response):
    return render(response, 'core/about.html')

@login_required(login_url='login')
def webinar_detail(response, pk):
    webinar = get_object_or_404(Webinar, pk=pk)
    
    is_registered = False
    if response.user.is_authenticated:
        is_registered = WebinarRegistration.objects.filter(
            webinar=webinar, 
            email=response.user.email
        ).exists()

    if response.method == 'POST':
        form = WebinarRegistrationForm(response.POST, response.FILES)
        if form.is_valid():
            if is_registered:
                messages.error(response, 'You are already registered for this webinar!')
                return redirect('webinar_detail', pk=webinar.pk)
            
            registration = form.save(commit=False)
            registration.webinar = webinar
            registration.status = "pending"
            
            if response.user.is_authenticated:
                registration.full_name = f"{response.user.first_name} {response.user.last_name}"
                registration.email = response.user.email
            
            registration.save()
            
            messages.success(response, 'Your registration was successful!')
            return redirect('webinar_detail', pk=webinar.pk)
        
    else:
        form = WebinarRegistrationForm()

        context = {
            'webinar': webinar,
            'form': form,
            'is_registered': is_registered,
            'now': timezone.now(),
        }
        return render(response, 'webinar/details.html', context)

@login_required(login_url='login')
def webinar_register(response, pk):
    webinar = Webinar.objects.get(id=pk)
    if response.method == "POST":
        form = WebinarRegistrationForm(response.POST)
        if form.is_valid():
            n = f"{response.user.first_name} {response.user.last_name}"
            e = f"{response.user.email}"
            c = form.cleaned_data["question"]
            status = "pending"
            payment_reference = form.cleaned_data.get('payment_reference')
            WebinarRegistration.objects.create(
                webinar=webinar,
                full_name=n,
                email=e,
                question=c,
                status=status,
                payment_reference=payment_reference,
            )
            return redirect('webinar_register', pk=pk)

    else:
        form = WebinarRegistrationForm()
        return render(response, 'webinar/register.html', {'webinar':webinar, 'form':form})