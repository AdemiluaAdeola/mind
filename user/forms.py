from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django_countries.widgets import CountrySelectWidget

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'bio', 'country', 'address', 'dob', 'gender', 
            'whatsapp', 'instagram', 'twitter', 'linkedin'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'country': CountrySelectWidget(attrs={
                'class': 'form-select'
            }),
            'address': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Your full address...'
            }),
        }
        help_texts = {
            'whatsapp': 'Enter your WhatsApp number with country code (e.g., +1234567890)',
        }