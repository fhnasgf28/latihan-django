from django.urls import path
from .views import notes_list_create

urlpatterns = [
    path("notes/", notes_list_create),
]