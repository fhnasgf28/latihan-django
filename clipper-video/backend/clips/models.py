import uuid
import secrets
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
        ('canceled', 'Canceled'),
    ]

    MODE_CHOICES = [
        ('auto', 'Auto'),
        ('manual', 'Manual'),
    ]

    SOURCE_CHOICES = [
        ('youtube', 'YouTube'),
        ('local', 'Local'),
    ]

    ORIENTATION_CHOICES = [
        ('landscape', 'Landscape'),
        ('portrait', 'Portrait'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_type = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='youtube')
    youtube_url = models.TextField(blank=True, default='')
    local_video_path = models.TextField(blank=True, default='')
    local_video_name = models.CharField(max_length=255, blank=True, default='')
    mode = models.CharField(max_length=10, choices=MODE_CHOICES)
    interval_minutes = models.IntegerField(null=True, blank=True)
    ranges = models.JSONField(null=True, blank=True)
    strict_1080 = models.BooleanField(default=False)
    min_height_fallback = models.IntegerField(default=720)
    subtitle_langs = models.JSONField(default=list)
    burn_subtitles = models.BooleanField(default=False)
    auto_captions = models.BooleanField(default=False)
    auto_caption_lang = models.CharField(max_length=10, default='id')
    whisper_model = models.CharField(max_length=10, default='small')
    subtitle_font = models.CharField(max_length=100, default='Arial')
    subtitle_size = models.IntegerField(default=28)
    burn_word_level = models.BooleanField(default=False, help_text="Burn word-level precision subtitles (per-word ASR)")
    orientation = models.CharField(max_length=10, choices=ORIENTATION_CHOICES, default='landscape')
    max_clips = models.IntegerField(default=0)
    download_sections = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='queued')
    progress = models.IntegerField(default=0)
    message = models.TextField(blank=True, default='')
    error = models.TextField(null=True, blank=True)
    cancel_requested = models.BooleanField(default=False)
    celery_task_id = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    access_token = models.CharField(max_length=64, unique=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.access_token:
            self.access_token = secrets.token_urlsafe(64)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Job {self.id} ({self.status})"
