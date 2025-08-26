from django.db import models
from django.contrib.auth.models import User
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils.text import slugify
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from django.core.exceptions import ValidationError
from datetime import timedelta
from django.utils import timezone

# Create your models here.

class TimestampModel(models.Model):
    """Abstract base model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Category(TimestampModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order in lists")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog_category', kwargs={'slug': self.slug})

class Tag(TimestampModel):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Blog(TimestampModel):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Published', 'Published'),
        ('Archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        related_name='blogs', 
        null=True, 
        blank=True
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='blogs')
    excerpt = models.TextField(
        blank=True, 
        help_text="Brief summary of the blog post (max 300 characters)"
    )
    content = RichTextUploadingField()
    featured_image = models.ImageField(
        upload_to='blog_images/%Y/%m/%d/', 
        blank=True, 
        null=True,
        help_text="Recommended size: 1200x675 pixels"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='blogs'
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='Draft'
    )
    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    allow_comments = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_verified']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Blog.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})
    
    def get_read_time(self):
        """Calculate estimated read time in minutes"""
        # Approx 200 words per minute
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))
    
    def clean(self):
        """Custom validation"""
        if self.status == 'Published' and not self.is_verified:
            raise ValidationError("Blog posts must be verified before publishing.")
        
        if len(self.excerpt) > 300:
            raise ValidationError("Excerpt cannot exceed 300 characters.")

class Comment(TimestampModel):
    blog = models.ForeignKey(
        Blog, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='comments'
    )
    content = models.TextField(max_length=1000)
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    is_approved = models.BooleanField(default=False)
    likes = models.ManyToManyField(
        User, 
        through='CommentLike', 
        related_name='liked_comments'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['blog', 'is_approved']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.blog.title}"
    
    def get_likes_count(self):
        return self.likes.count()

class CommentLike(TimestampModel):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('comment', 'user')

class Speaker(TimestampModel):
    name = models.CharField(max_length=100)
    bio = models.TextField(help_text="Brief biography of the speaker")
    photo = models.ImageField(
        upload_to='speaker_photos/%Y/%m/%d/', 
        blank=True, 
        null=True
    )
    website = models.URLField(blank=True)
    twitter = models.CharField(max_length=100, blank=True)
    linkedin = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Webinar(TimestampModel):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('live', 'Live'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=200, blank=True)
    description = models.TextField()
    featured_image = models.ImageField(
        upload_to='webinar_images/%Y/%m/%d/',
        help_text="Recommended size: 1200x675 pixels"
    )
    start_datetime = models.DateTimeField()
    duration = models.PositiveIntegerField(
        help_text="Duration in minutes",
        validators=[MinValueValidator(5), MaxValueValidator(480)]  # 5min to 8 hours
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='upcoming'
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0
    )
    capacity = models.PositiveIntegerField(default=100)
    is_featured = models.BooleanField(default=False)
    host = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='hosted_webinars'
    )
    speakers = models.ManyToManyField(
        Speaker, 
        through='WebinarSpeaker', 
        related_name='webinars'
    )
    meeting_url = models.URLField(blank=True, help_text="Zoom/Google Meet link")
    recording_url = models.URLField(blank=True, help_text="Link to webinar recording")
    
    class Meta:
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['status', 'start_datetime']),
        ]

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure slug is unique
            original_slug = self.slug
            counter = 1
            while Webinar.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('webinar_detail', kwargs={'slug': self.slug})

    @property
    def is_free(self):
        return self.price == 0

    @property
    def seats_remaining(self):
        return self.capacity - self.registrations.filter(status='confirmed').count()
    
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

class WebinarSpeaker(TimestampModel):
    webinar = models.ForeignKey(Webinar, on_delete=models.CASCADE)
    speaker = models.ForeignKey(Speaker, on_delete=models.CASCADE)
    is_main_speaker = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order']
        unique_together = ('webinar', 'speaker')

# class WebinarRegistration(TimestampModel):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('confirmed', 'Confirmed'),
#         ('cancelled', 'Cancelled'),
#         ('attended', 'Attended'),
#     ]

#     webinar = models.ForeignKey(
#         Webinar, 
#         on_delete=models.CASCADE, 
#         related_name='registrations'
#     )
#     full_name = models.CharField(
#         max_length=2555555
#     )
#     email = models.EmailField()
#     status = models.CharField(
#         max_length=10, 
#         choices=STATUS_CHOICES, 
#         default='pending'
#     )
#     payment_reference = models.CharField(max_length=100, blank=True)
#     attendance_confirmed = models.BooleanField(default=False)
#     questions = models.TextField(
#         blank=True, 
#         verbose_name="Any questions for the speakers"
#     )
#     joined_at = models.DateTimeField(null=True, blank=True)
#     left_at = models.DateTimeField(null=True, blank=True)
    
#     class Meta:
#         unique_together = ('webinar', 'email')
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"{self.email} - {self.webinar.title}"
    
#     @property
#     def attendance_duration(self):
#         if self.joined_at and self.left_at:
#             return (self.left_at - self.joined_at).total_seconds() / 60
#         return 0
    
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
    attendance_confirmed = models.BooleanField(default=False)
    question = models.TextField(verbose_name="Any questions for the speaker")
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    payment_reference = models.FileField(upload_to="payment")
    
    class Meta:
        unique_together = ('webinar', 'email')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.webinar.title}"
    
    @property
    def attendance_duration(self):
        if self.joined_at and self.left_at:
            return (self.left_at - self.joined_at).total_seconds() / 60
        return 0

class WebinarResource(TimestampModel):
    RESOURCE_TYPES = [
        ('slide', 'Presentation Slides'),
        ('video', 'Video'),
        ('document', 'Document'),
        ('link', 'External Link'),
        ('other', 'Other'),
    ]
    
    webinar = models.ForeignKey(
        Webinar, 
        on_delete=models.CASCADE, 
        related_name='resources'
    )
    title = models.CharField(max_length=200)
    resource_type = models.CharField(
        max_length=10, 
        choices=RESOURCE_TYPES, 
        default='document'
    )
    file = models.FileField(
        upload_to='webinar_resources/%Y/%m/%d/', 
        blank=True, 
        null=True
    )
    url = models.URLField(blank=True)
    is_preview = models.BooleanField(
        default=False,
        help_text="Available to everyone (not just attendees)"
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title
    
    def clean(self):
        """Ensure either file or URL is provided"""
        if not self.file and not self.url:
            raise ValidationError("Either file or URL must be provided.")
        if self.file and self.url:
            raise ValidationError("Cannot have both file and URL. Choose one.")