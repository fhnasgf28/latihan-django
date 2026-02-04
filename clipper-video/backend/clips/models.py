import uuid

from django.db import models
from django.contrib.auth.models import User

class Video(models.Model):
    """Model untuk video yang akan di-clip"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video_file = models.FileField(upload_to='videos/')
    duration = models.FloatField(help_text="Duration in seconds")
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Clip(models.Model):
    """Model untuk clip yang di-buat dari video"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='clips')
    start_time = models.FloatField(help_text="Start time in seconds")
    end_time = models.FloatField(help_text="End time in seconds")
    thumbnail = models.ImageField(upload_to='clip_thumbnails/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Job(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ]

    MODE_CHOICES = [
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    youtube_url = models.TextField()
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    interval_minutes = models.IntegerField(null=True, blank=True)
    ranges = models.JSONField(null=True, blank=True)
    strict_1080 = models.BooleanField(default=False)
    min_height_fallback = models.IntegerField(default=720)
    subtitle_langs = models.JSONField(default=list)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='queued')
    progress = models.IntegerField(default=0)
    message = models.TextField(blank=True, default='')
    error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} ({self.status})"
