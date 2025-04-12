from django.db import models

class FoodItem(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class Order(models.Model):
    customer_name = models.CharField(max_length=100)
    food_items = models.ManyToManyField(FoodItem)
    order_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order by {self.customer_name} on {self.order_date.strftime('%Y-%m-%d %H:%M:%S')}"
