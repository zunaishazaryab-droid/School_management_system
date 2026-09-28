from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class ItemCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Item Category")
        verbose_name_plural = _("Item Categories")
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Supplier")
        verbose_name_plural = _("Suppliers")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.phone})"


class InventoryItem(models.Model):
    UNIT_CHOICES = [
        ('PCS', 'Pieces (Pcs)'),
        ('BOX', 'Boxes'),
        ('PKT', 'Packets'),
        ('REAM', 'Paper Reams'),
        ('SET', 'Sets'),
        ('KG', 'Kilograms (Kg)'),
        ('LTR', 'Liters (Ltr)'),
        ('UNIT', 'Units'),
    ]

    name = models.CharField(max_length=200)
    item_code = models.CharField(max_length=50, unique=True, help_text="SKU or Item Code")
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, related_name='items')
    quantity_in_stock = models.IntegerField(default=0)
    min_reorder_level = models.IntegerField(default=5, help_text="Threshold for low-stock warning")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='PCS')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Estimated unit cost")
    location = models.CharField(max_length=100, blank=True, null=True, help_text="Store room, shelf or cabinet")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Inventory Item")
        verbose_name_plural = _("Inventory Items")
        ordering = ['name']

    def __str__(self):
        return f"{self.name} [{self.item_code}] - {self.quantity_in_stock} {self.get_unit_display()}"

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.min_reorder_level

    @property
    def total_valuation(self):
        return self.quantity_in_stock * self.unit_price


class StockTransaction(models.Model):
    class Type(models.TextChoices):
        IN = 'IN', _('Stock IN (Purchase/Restock)')
        OUT = 'OUT', _('Stock OUT (Issuance/Consumption)')

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=Type.choices, default=Type.IN)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_purchases')
    issued_to = models.CharField(max_length=150, blank=True, null=True, help_text="Department, Teacher, or Staff person who received the items")
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="Invoice or requisition number")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    transaction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Stock Transaction")
        verbose_name_plural = _("Stock Transactions")
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.quantity} x {self.item.name} on {self.transaction_date}"

    @property
    def total_cost(self):
        return self.quantity * self.unit_price
