# pos_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='pos_index'),
    path('success/<int:transaction_id>/', views.success, name='pos_success'),
]
