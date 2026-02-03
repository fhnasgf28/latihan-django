from django.urls import path
from .views import youtube_download

urlpatterns = [
    path("youtube/download/", youtube_download),
]
