from django.urls import path
from .views import menu_list, order_create, order_success

urlpatterns = [
    path('', menu_list, name='menu_list'),
    path('order/', order_create, name='order_create'),
    path('order/success/', order_success, name='order_success'),
]