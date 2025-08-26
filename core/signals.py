from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import *

@receiver(pre_save, sender=Webinar)
def update_webinar_status(sender, instance, **kwargs):
    """Automatically update webinar status based on datetime"""
    now = timezone.now()
    if instance.start_datetime and instance.duration:
        end_time = instance.start_datetime + timedelta(minutes=instance.duration)
        
        if instance.status != 'cancelled':
            if now > end_time:
                instance.status = 'completed'
            elif instance.start_datetime <= now <= end_time:
                instance.status = 'live'
            else:
                instance.status = 'upcoming'

@receiver(post_save, sender=Blog)
def send_verification_notification(sender, instance, created, **kwargs):
    """Send notification when a blog post is ready for verification"""
    if instance.status == 'Published' and not instance.is_verified:
        # Here you would typically send an email to admins
        # For now, we'll just print to console
        print(f"Blog '{instance.title}' needs verification!")