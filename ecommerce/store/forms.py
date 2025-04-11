from django import forms
from .models import Product

class ProductForm(forms.ModelForm): 
    class Meta:
        model = Product 
        fields = ['name', 'description', 'price', 'stock', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 15}),
        }

class CheckoutForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=100)