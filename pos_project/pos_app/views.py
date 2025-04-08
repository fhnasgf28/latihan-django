from django.shortcuts import render, redirect
from .models import Product, Transaction, TransactionItem
from .forms import TransactionForm
from decimal import Decimal

def index (request):
    if Product.objects.count() == 0:
        Product.objects.create(name='Product 1', price=Decimal('10.00'))
        Product.objects.create(name='Product 2', price=Decimal('20.00'))
        Product.objects.create(name='Product 3', price=Decimal('30.00'))
    form = TransactionForm()
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']
            subtotal = product.price * quantity

            transaction = Transaction.objects.create(total=subtotal)
            TransactionItem.objects.create(transaction=transaction, product=product, quantity=quantity, subtotal=subtotal)
            return redirect('pos_success', transaction_id=transaction.id)
    return render(request, 'pos_app/index.html', {'form': form})

def success(request, transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    items = transaction.items.all()
    total = sum(item.subtotal for item in items)
    return render(request, 'pos_app/success.html', {'transaction': transaction, 'items': items, 'total': total})