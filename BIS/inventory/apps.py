from django.apps import AppConfig
from django.db.models.signals import post_delete , post_save


class InventoryConfig(AppConfig):
    name = 'inventory'

    def ready(self):
        from .models import InventoryPrice, InventoryReturn
        from .signals import (
            purchase_inventory_update,update_purchase_after_inventory_return,
            update_purchase_after_pay_invoice, update_purchase_after_pay_invoice_delete,
            update_purchase_after_allowance, update_purchase_after_allowance_delete
        )
        from sole_proprietorship.models import Transaction

        post_delete.connect(purchase_inventory_update, sender='inventory.InventoryPrice')
        post_save.connect(Transaction.signal.PurchaseInventory, sender='inventory.InventoryPrice')
        post_save.connect(Transaction.signal.freight_in_cost, sender='inventory.InventoryPrice')


        post_save.connect(Transaction.signal.PurchaseReturn, sender='inventory.InventoryReturn')
        post_save.connect(update_purchase_after_pay_invoice, sender='inventory.PayInvoice')
        post_delete.connect(update_purchase_after_pay_invoice_delete, sender='inventory.PayInvoice')

        post_save.connect(purchase_inventory_update, sender='inventory.InventoryPrice')
        post_save.connect(update_purchase_after_inventory_return, sender='inventory.InventoryReturn')

        post_save.connect(Transaction.signal.purchase_allowance, sender='inventory.InventoryAllowance')
        post_save.connect(update_purchase_after_allowance, sender='inventory.InventoryAllowance')

        post_delete.connect(update_purchase_after_allowance_delete, sender='inventory.InventoryAllowance')
        post_save.connect(Transaction.signal.sale, sender='inventory.Sold_Item')
        post_save.connect(Transaction.signal.sale_return, sender='inventory.SalesReturn')
        post_save.connect(Transaction.signal.sale_allowance, sender='inventory.SalesAllowance')
        post_save.connect(Transaction.signal.received_payment, sender='inventory.SalesPayment')

