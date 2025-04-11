from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('product_list/', views.product_list, name='product_list'),
    path('add_product/', views.add_product, name='add_product'),
    path('view_cart/', views.view_cart, name='view_cart'),
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('transaction_history/', views.transaction_history, name='transaction_history'),
]