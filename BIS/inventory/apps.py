from django.apps import AppConfig
from django.db.models.signals import post_delete , post_save


class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        from .models import InventoryPrice, InventoryReturn
        from .signals import (inventory_price_journal_delete, purchase_return_journal_save, inventory_price_journal_save,
            purchase_return_journal_delete, freight_in_cost, purchase_inventory_update,update_purchase_after_inventory_return,
            update_purchase_after_pay_invoice
        )

        post_delete.connect(inventory_price_journal_delete, sender='inventory.InventoryPrice')
        post_save.connect(inventory_price_journal_save, sender='inventory.InventoryPrice')
        post_save.connect(freight_in_cost, sender='inventory.InventoryPrice')


        post_delete.connect(purchase_return_journal_delete, sender='inventory.InventoryReturn')
        post_save.connect(purchase_return_journal_save, sender='inventory.InventoryReturn')
        post_save.connect(update_purchase_after_pay_invoice, sender='inventory.PayInvoice')
        post_save.connect(purchase_inventory_update, sender='inventory.InventoryPrice')
        post_save.connect(update_purchase_after_inventory_return, sender='inventory.InventoryReturn')

