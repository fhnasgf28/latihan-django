from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Create your models here.
class Customer(models.Model):
    name = models.charField(max_length=150)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self) -> str:
        return self.name

class Product(models.Model):
    name = models.charField(max_length=150)
    sku = models.CharField(max_lentgth=50, unique=True)
    price = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

class SalesOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_lentgth=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_amount(self):
        return sum((line.subtotal for line in self.lines.all()), Decimal("0"))

    def __str__(self) -> str:
        return self.number

class SalesOrderLine(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name ="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    price_unit = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])

    @property
    def subtotal(self):
        return (self.qty * self.price_unit)

    def __str__(self) -> str:
        return f"{self.order.number} - {self.product.name}"