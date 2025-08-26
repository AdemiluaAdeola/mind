from django import forms
from .models import *
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from user.models import Profile
from django_countries.widgets import CountrySelectWidget

# class WebinarRegistrationForm(forms.ModelForm):
#     class Meta:
#         model=WebinarRegistration
#         fields = [
#             'first_name',
#             'last_name',
#             'email',
#             'attendance_confirmed',
#             'question'
#         ]

class BlogForm(forms.ModelForm):
    categories = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="Select category"
    )
    
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    publish_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text="Schedule publication for a future date"
    )
    
    class Meta:
        model = Blog
        fields = [
            'title', 'category', 'tags', 'excerpt', 'content', 
            'featured_image', 'status', 'meta_title', 'meta_description',
            'allow_comments'
        ]
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'meta_description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Make specific fields not required
        self.fields['featured_image'].required = False
        self.fields['meta_title'].required = False
        self.fields['meta_description'].required = False

class WebinarForm(forms.ModelForm):
    start_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%m-%d-%YT%H:%M']
    )
    
    class Meta:
        model = Webinar
        fields = [
            'title', 'description', 'featured_image', 'start_datetime', 
            'duration', 'status', 'price', 'capacity', 'is_featured',
            'meeting_url', 'recording_url', 'speakers'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'speakers': forms.CheckboxSelectMultiple,
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
        
        # Set initial datetime to current time if creating new
        if not self.instance.pk:
            self.fields['start_datetime'].initial = timezone.now()
        
        # Make specific fields not required
        self.fields['featured_image'].required = False
        self.fields['meeting_url'].required = False
        self.fields['recording_url'].required = False
    
    def clean_start_datetime(self):
        start_datetime = self.cleaned_data.get('start_datetime')
        if start_datetime and start_datetime < timezone.now():
            raise forms.ValidationError("Start datetime cannot be in the past.")
        return start_datetime

class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        fields = ['name', 'bio', 'photo', 'website', 'twitter', 'linkedin', 'email', 'is_active']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})

class WebinarResourceForm(forms.ModelForm):
    class Meta:
        model = WebinarResource
        fields = ['title', 'resource_type', 'file', 'url', 'is_preview', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')
        
        if not file and not url:
            raise forms.ValidationError("Either file or URL must be provided.")
        
        return cleaned_data
    
class UserCreationFormExtended(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'groups', 'is_staff', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})

class UserForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'groups', 'is_staff', 'is_active', 'is_superuser']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({'class': 'form-control'})

class ProfileForm(forms.ModelForm):
    GENDER_CHOICES = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Others", "Others"),
    )
    
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Date of birth"
    )
    
    class Meta:
        model = Profile
        fields = ['bio', 'country', 'address', 'dob', 'profile_picture', 'gender', 'whatsapp', 'instagram', 'twitter', 'linkedin']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
            'country': CountrySelectWidget(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                if field_name != 'country':  # Country widget has its own class
                    field.widget.attrs.update({'class': 'form-control'})
        
        # Make fields not required
        for field in self.fields:
            self.fields[field].required = False
    
    def clean_whatsapp(self):
        whatsapp = self.cleaned_data.get('whatsapp')
        if whatsapp and len(str(whatsapp)) > 15:
            raise forms.ValidationError("WhatsApp number is too long.")
        return whatsapp