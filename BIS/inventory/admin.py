from django.contrib import admin
from inventory.models import Inventory , InventoryPrice , PaymentTerm , PurchaseInventory 
# Register your models here.
admin.site.register(Inventory)
admin.site.register(InventoryPrice)
admin.site.register(PaymentTerm)
admin.site.register(PurchaseInventory)
