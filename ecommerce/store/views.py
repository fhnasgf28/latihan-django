from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Product, Transaction, Cart
from .forms import ProductForm, CheckoutForm

@login_required
def product_list(request):
    products = Product.objects.filter(stock__gt=0).exclude(seller=request.user)
    return render(request, 'store/product_list.html', {'products': products})

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            return redirect('product_list')
    else:
        form = ProductForm()
    return render(request, 'store/add_product.html', {'form': form})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product, defaults={'quantity': 1})
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render(request, 'store/cart.html', {'cart_items': cart_items, 'total': total})

@login_required
def checkout(request):
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        for item in cart_items:
            if item.product.stock < item.quantity:
                return render(request, 'store/error.html', {
                    'message': f"stock {item.product.name} tidk mncul"
                })
            
            Transaction.objects.create(
                buyer=request.user,
                product=item.product,
                quantity=item.quantity,
                total_price=item.product.price * item.quantity,
                status = 'completed'
            )

            item.product.stock -= item.quantity
            item.product.save()
            item.delete()
        return redirect('transaction_history')
    return redirect('view_cart')