from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField

# Create your models here.
class Profile(models.Model):
    gender_choices = (
        ("Male", "Male"),
        ("Female", "Female"),
        ("Others", "Others"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    country = CountryField(blank_label='(select country)')
    address = models.TextField(blank=True)
    dob = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures', blank=True)
    gender = models.CharField(max_length=20, choices=gender_choices)
    whatsapp = models.PositiveBigIntegerField()
    instagram = models.URLField()
    twitter = models.URLField()
    linkedin = models.URLField(verbose_name="LinkedIn")
    
    def __str__(self):
        return self.user.username
