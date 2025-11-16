from django import forms
from .models import *
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div

class CreateNewPost(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'author', 'snippet', 'body', 'cover', 'status', 'is_verified']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'author': forms.TextInput(attrs={'value':'', 'id':'blogger', 'type':'hidden'}),
            'snippet':forms.Textarea(attrs={'class':'form-control'}),
        }

class UpdatePost(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['title', 'author', 'snippet', 'body', 'cover', 'status', 'is_verified']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'author': forms.TextInput(attrs={'value':'', 'id':'blogger', 'type':'hidden'}),
            'snippet':forms.Textarea(attrs={'class':'form-control'}),
        }

class CommentSection(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            'body':forms.Textarea(attrs={'rows':10, 'col':25}),
        }

class CreateWebinar(forms.ModelForm):
    class Meta:
        model=Webinar
        fields = [
            'title',
            'description',
            'featured_image',
            'start_datetime',
            'duration',
            'price',
            'is_featured',
            'host',
            'speakers',
            'meeting_url',
            'recording_url',
        ]

class WebinarRegistrationForm(forms.ModelForm):
    class Meta:
        model = WebinarRegistration
        fields = [
            # 'full_name',
            # 'email',
            # 'status',
            'question',
            'payment_reference'
        ]
        widgets = {
            'question': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What questions would you like to ask the speaker?'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = WebinarRegistration
        fields = ['full_name', 'email', 'status', 'question']
        widgets = {
            'question': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})