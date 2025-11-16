from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from user.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone
from cloudinary.models import CloudinaryField

# Create your models here.

class TimestampModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

class Blog(TimestampModel):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Archived', 'Archived'),
    ]

    # Updated to CloudinaryField with optimizations
    cover = CloudinaryField(
        'image',
        folder='blog/covers/',
        transformation={
            'quality': 'auto:good',
            'width': 1200,
            'height': 675,
            'crop': 'fill'
        },
        format='webp',
        help_text="Recommended size: 1200x675 pixels"
    )
    title = models.CharField(max_length=100000)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    snippet = models.TextField()
    body = RichTextUploadingField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['is_verified', 'status']),
        ]

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'pk': self.id})
    
    @property
    def cover_thumbnail(self):
        """Generate thumbnail URL for the cover image"""
        if self.cover:
            return self.cover.build_url(width=300, height=200, crop='fill', quality='auto')
        return None
    
    @property
    def cover_optimized(self):
        """Generate optimized URL for web display"""
        if self.cover:
            return self.cover.build_url(width=800, height=450, crop='fill', quality='auto', format='webp')
        return None
    
    @property
    def is_published(self):
        return self.status == 'Published' and self.is_verified
    
    def get_related_blogs(self, limit=3):
        """Get related blogs by category"""
        return Blog.objects.filter(
            category=self.category,
            status='Published',
            is_verified=True
        ).exclude(id=self.id)[:limit]

class Comment(TimestampModel):
    blog = models.ForeignKey(Blog, related_name="comments", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    body = models.TextField()
    
    # Add Cloudinary field for comment attachments
    attachment = CloudinaryField(
        'raw',
        folder='blog/comments/attachments/',
        blank=True,
        null=True,
        help_text="Optional file attachment for the comment"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Comment'
        verbose_name_plural = 'Blog Comments'

    def __str__(self):
        return f"Comment by {self.name} on {self.blog.title}"

class Speaker(TimestampModel):
    name = models.CharField(max_length=100)
    bio = models.TextField(help_text="Brief biography of the speaker")
    
    # Updated to CloudinaryField
    photo = CloudinaryField(
        'image',
        folder='speakers/photos/',
        transformation={
            'quality': 'auto:good',
            'width': 400,
            'height': 400,
            'crop': 'fill',
            'gravity': 'face'
        },
        format='webp',
        blank=True,
        null=True,
        help_text="Speaker profile photo - Recommended: 400x400 pixels"
    )
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Speaker'
        verbose_name_plural = 'Speakers'
    
    def __str__(self):
        return self.name
    
    @property
    def photo_thumbnail(self):
        """Generate thumbnail URL for speaker photo"""
        if self.photo:
            return self.photo.build_url(width=100, height=100, crop='fill', gravity='face')
        return None

class Webinar(TimestampModel):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Updated to CloudinaryField
    featured_image = CloudinaryField(
        'image',
        folder='webinars/featured/',
        transformation={
            'quality': 'auto:good',
            'width': 1200,
            'height': 675,
            'crop': 'fill'
        },
        format='webp',
        help_text="Recommended size: 1200x675 pixels"
    )
    start_datetime = models.DateTimeField()
    duration = models.PositiveIntegerField(
        help_text="Duration in minutes",
        validators=[MinValueValidator(5), MaxValueValidator(480)]
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='upcoming')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0
    )
    is_featured = models.BooleanField(default=False)
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hosted_webinars')
    speakers = models.ManyToManyField(Speaker, related_name='webinars')
    meeting_url = models.URLField(blank=True, help_text="Zoom/Google Meet link")
    recording_url = models.URLField(blank=True, help_text="Link to webinar recording")
    
    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['status', 'start_datetime']),
            models.Index(fields=['is_featured', 'status']),
        ]
        verbose_name = 'Webinar'
        verbose_name_plural = 'Webinars'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('webinar_detail', kwargs={'pk': self.id})

    @property
    def is_free(self):
        return self.price == 0
    
    @property
    def end_datetime(self):
        return self.start_datetime + timedelta(minutes=self.duration)
    
    def is_upcoming(self):
        return self.status == 'upcoming' and self.start_datetime > timezone.now()
    
    def is_live(self):
        now = timezone.now()
        return (self.status == 'live' or 
                (self.status == 'upcoming' and 
                 self.start_datetime <= now <= self.end_datetime))
    
    @property
    def featured_image_thumbnail(self):
        """Generate thumbnail URL for featured image"""
        if self.featured_image:
            return self.featured_image.build_url(width=400, height=225, crop='fill', quality='auto')
        return None

class WebinarRegistration(TimestampModel):
    status_choices = (
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("cancelled", "cancelled"),
    )

    webinar = models.ForeignKey(Webinar, related_name='registrations', on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(max_length=255, choices=status_choices)
    question = models.TextField(verbose_name="Any questions for the speaker", blank=True, null=True)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.FileField(upload_to="payment", verbose_name="Proof of Payment", blank=True, null=True)
    
    class Meta:
        unique_together = ('webinar', 'email')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.webinar.title}"