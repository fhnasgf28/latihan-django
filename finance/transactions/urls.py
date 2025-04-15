from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add/', views.add_transaction, name='add'),
    path('list/', views.transaction_list, name='list'),
]