from django.contrib import admin
from inventory.models import Inventory , InventoryPrice , PaymentSalesTerm , PurchaseInventory , InventoryImag
# Register your models here.
admin.site.register(Inventory)
admin.site.register(InventoryPrice)
admin.site.register(PaymentSalesTerm)
admin.site.register(PurchaseInventory)
admin.site.register(InventoryImag)
