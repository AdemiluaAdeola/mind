from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from datetime import date
from django_countries.fields import CountryField

# Create your models here.
class User(AbstractUser):
    gender_choices = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Others", "Others"),
    )

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    dob = models.DateField(blank=True, null=True)
    phone = models.CharField(
        max_length=15,
        verbose_name='Phone Number',
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")],
        blank=True, null=True
    )
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True)
    gender = models.CharField(max_length=20, choices=gender_choices)
    instagram = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    country = CountryField(blank_label='(select country)')
    location = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
    
    @property
    def age(self):
        if self.dob:
            today = date.today()
            return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        return None