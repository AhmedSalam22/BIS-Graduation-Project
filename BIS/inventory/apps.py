from django.apps import AppConfig
from django.db.models.signals import post_delete , post_save


class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        from .models import InventoryPrice, InventoryReturn
        from .signals import (inventory_price_journal_delete, purchase_return_journal_save, inventory_price_journal_save,
            purchase_return_journal_delete
        )

        post_delete.connect(inventory_price_journal_delete, sender='inventory.InventoryPrice')
        post_save.connect(inventory_price_journal_save, sender='inventory.InventoryPrice')

        post_delete.connect(purchase_return_journal_delete, sender='inventory.InventoryReturn')
        post_save.connect(purchase_return_journal_save, sender='inventory.InventoryReturn')
