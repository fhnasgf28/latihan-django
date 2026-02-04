from django.contrib import admin
from .models import Video, Clip, Job


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'duration', 'created_at']
    list_filter = ['created_at', 'uploaded_by']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ['title', 'video', 'created_by', 'start_time', 'end_time', 'is_public', 'created_at']
    list_filter = ['is_public', 'created_at', 'created_by']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['id', 'youtube_url', 'status', 'progress', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['youtube_url']
    readonly_fields = ['created_at', 'updated_at']
