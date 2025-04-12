from django.shortcuts import render, redirect
from .models import FoodItem, Order
from .form import OrderForm

def menu_list(request):
    items = FoodItem.objects.filter(available=True)
    return render(request, 'cafe/menu_list.html', {'items': items})

def order_create(request):
    if request.method == "POST":
        form = OrderForm(request.POST)
        order = form.save()
        return redirect('order_success')
    else:
        form = OrderForm()
    return render(request, 'cafe/order_form.html', {'form': form})

def order_success(request):
    return render(request, 'cafe/order_success.html')
