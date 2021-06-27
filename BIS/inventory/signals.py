from sole_proprietorship.models import Journal
from django.db.models import Q 
from inventory.helper import Helper






def purchase_inventory_update(sender, instance , created=None,  **kwargs):
    """
    Update this row after we purchase item and know their cost and quantity

    instance: InventoryPrice
    """
    purchase_inventory = instance.purchase_inventory
    purchase_inventory.total_purchases =  purchase_inventory.check_total_amount()
    purchase_inventory.net_purchases = purchase_inventory.check_net_purchase()
    purchase_inventory.total_amount_paid = purchase_inventory.check_total_amount_paid()
    purchase_inventory.status = 0 if purchase_inventory.check_status() =="UNPAID" else 1
    purchase_inventory.save()


def update_purchase_after_inventory_return(sender, instance , created,  **kwargs):
    """
    Update Purchase Inventory after return inventory

    instance: InventoryReturn
    """
    purchaseinventory = instance.inventory_price.purchase_inventory
    purchaseinventory.status = 0 if purchaseinventory.check_status() =="UNPAID" else 1
    purchaseinventory.num_returend , purchaseinventory.cost_returned =  purchaseinventory.check_num_cost_of_returned_inventory()
    purchaseinventory.net_purchases = purchaseinventory.check_net_purchase()
    # purchaseinventory.total_amount_paid
    purchaseinventory.save()



def update_purchase_after_pay_invoice(sender, instance , created,  **kwargs):
    """
    Update Purchase after Pay Invoice
    instance: PayInvoice
    """
    purchase_inventory = instance.purchase_inventory
    purchase_inventory.total_amount_paid = purchase_inventory.check_total_amount_paid()
    purchase_inventory.status = 1 if purchase_inventory.check_status() == "PAID" else 0
    purchase_inventory.save()


