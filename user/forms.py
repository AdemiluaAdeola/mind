from django import forms
from .models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Field, Div

#forms
class UserForm(forms.ModelForm):
    class Meta:
        model=User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            "profile_picture",
            "country",
            "location",
            "bio",
            "dob",
            "gender",
            "facebook",
            "instagram",
            "twitter",
            "linkedin"
        ]

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'bio', 'dob', 'gender', 'phone', 
                 'profile_picture', 'country', 'location', 'instagram', 'twitter', 
                 'facebook', 'linkedin']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.add_input(Submit('submit', 'Update Profile'))