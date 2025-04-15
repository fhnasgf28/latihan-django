from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Transaction, Category
from .forms import TransactionForm
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import csv
from django.http import HttpResponse

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    return render(request, 'transactions/dashboard.html', {'transactions': transactions})

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            return redirect('transactions:dashboard')
    else:
        form = TransactionForm()
    return render(request, 'transactions/add_transaction.html', {'form': form})

@login_required
def dashboard(request):
    transactions = Transaction.objects.filter(user=request.user)
    # hitung total pemasukan dan pengeluaran
    total_income = sum(t.amount for t in transactions if t.transaction_type == 'income')
    total_expense = sum(t.amount for t in transactions if t.transaction_type == 'expense')

    # buat grafik
    plt.figure(figsize=(6, 4))
    plt.bar(['Income', 'Expense'], [total_income, total_expense], color=['green', 'red'])
    plt.title('Total Income vs Expense')

    # konversi grafik ke base64 untuk html
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    chart = base64.b64encode(buffer.read()).decode('utf-8')

    return render(request, 'transactions/dashboard.html', {
        'transactions': transactions,
        'chart': chart,
        'total_income': total_income,
        'total_expense': total_expense,
    })

@login_required
def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tanggal', 'Kategori', 'Jumlah', 'Deskripsi'])
    transactions = Transaction.objects.filter(user=request.user)
    for t in transactions:
        writer.writerow([t.date, t.category.name, t.amount, t.description])
    return response
