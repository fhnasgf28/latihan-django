from django.contrib import admin
from .models import Customer, Product, SalesOrder, SalesOrderLine
# Register your models here.

class SalesOrderLineInLine(admin.TabularInline):
    model = SalesOrderLine
    extra = 1

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ("number", "customer", "status", "total_amount", "created_at")
    list_filter = ("status","created_at")
    search_fields = ("number", "customer__name")
    inlines = [SalesOrderLineInLine]

admin.site.register(Customer)
admin.site.register(Product)

