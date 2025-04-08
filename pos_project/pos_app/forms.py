from django import forms
from .models import Product

class TransactionForm(forms.Form):

    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        empty_label=None,  # untuk tidak ada "--pilih--"
        widget=forms.Select()
    )
    quantity = forms.IntegerField(min_value=1, label="Quantity")
    payment_method = forms.ChoiceField(choices=[('cash', 'Cash'), ('card', 'Card')], label="Payment Method")