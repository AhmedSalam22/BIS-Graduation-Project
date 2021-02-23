from sole_proprietorship.models import Journal
from django.db.models import Q 

def inventory_price_journal_delete(sender, instance, **kwargs):
    """Delete journal transaction related to inventory price"""
    Journal.objects.filter(
            Q(inventory_price=instance) & Q(status=Journal.Status.PURCHASE_INVENTORY.value) 
            ).delete()


def purchase_return_journal_delete(sender, instance, **kwargs):
    """Delete Journal transaction related to Purchase Inventory"""
    Journal.objects.filter(
        Q(inventory_return=instance) & Q(status=Journal.Status.PURCHASE_RETURN.value) 
    ).delete()



def purchase_return_journal_save(sender, instance , created,  **kwargs):
    """
    Journal transaxtion related to purchase return
        A/P or CASH Debit by xxx
        Inventory Credit by     xxx

    instance: InventoryReturn
    """
    owner = instance.inventory_price.inventory.owner
    date = instance.date
    balance = instance.num_returned * instance.inventory_price.cost_per_unit

    if not created:
        Journal.objects.filter(
            Q(inventory_return=instance) & Q(status=Journal.Status.PURCHASE_RETURN.value) 
        ).delete()

    Journal.objects.create(
            owner=owner,
            account = instance.inventory_price.inventory.general_ledeger_account,
            date = date ,
            balance= balance,
            transaction_type="Credit" , 
            comment=f"return inventory",
            inventory_return = instance,
            status=Journal.Status.PURCHASE_RETURN.value
            )
    Journal.objects.create(owner=owner,
                account = instance.inventory_price.purchase_inventory.term.general_ledeger_account,
                date = date ,
                balance=  balance ,
                transaction_type="Debit" , 
                comment=f"return {instance.num_returned} from {instance.inventory_price.inventory} to {instance.inventory_price.purchase_inventory.supplier}",
                inventory_return = instance,
                status=Journal.Status.PURCHASE_RETURN.value
                )


def inventory_price_journal_save(sender, instance , created,  **kwargs):
    """"
        Purchase Inventory transaction:
        transaction1:Inventory Debit by                      xxxx
        transaction2:     Cash or Accounts payable Credit by       xxx
    
    instance: InventoryPrice
    """

    owner = instance.purchase_inventory.owner
    purchase_inventory = instance.purchase_inventory
    inventory_price = instance

    if not created:
        Journal.objects.filter(
            Q(inventory_price=inventory_price) & Q(status=Journal.Status.PURCHASE_INVENTORY.value) 
            ).delete()

        
    Journal.objects.create(owner=owner,
            account = inventory_price.inventory.general_ledeger_account,
            date = purchase_inventory.purchase_date ,
            balance= inventory_price.number_of_unit *  inventory_price.cost_per_unit ,
            transaction_type="Debit" , 
            purchase_inventory = purchase_inventory,
            inventory_price = inventory_price,
            status = 1,
            comment=f"purchase inventory {inventory_price.inventory}, number of units purchased{inventory_price.number_of_unit}")
    Journal.objects.create(owner=owner,
                account = purchase_inventory.term.general_ledeger_account,
                date = purchase_inventory.purchase_date ,
                balance= inventory_price.number_of_unit *  inventory_price.cost_per_unit ,
                transaction_type="Credit" , 
                purchase_inventory = purchase_inventory,
                inventory_price = inventory_price,
                status = 1,
                comment=f"purchase {inventory_price.inventory}")


def freight_in_cost(sender, instance , created,  **kwargs):
    """
    - record journal transaction if there is freight cost due to the purchase process
    - fright-in charge will charge of first inventory form in formset

    instance: InventoryPrice
    """
    owner = instance.purchase_inventory.owner
    date = instance.purchase_inventory.purchase_date
    balance = instance.purchase_inventory.frieght_in

    exists = Journal.objects.filter(
        Q(purchase_inventory = instance.purchase_inventory) & Q(status=Journal.Status.FREIGHT_IN.value) 
        ).exists()

    if not exists and balance != 0:
        Journal.objects.create(owner=owner,
                account = instance.inventory.general_ledeger_account,
                date = date ,
                balance= balance ,
                transaction_type="Debit" , 
                status= Journal.Status.FREIGHT_IN.value,
                purchase_inventory = instance.purchase_inventory,
                comment=f"freight in cost {instance.inventory}")
        Journal.objects.create(owner=owner,
                    account = instance.purchase_inventory.term.freight_in_account,
                    date = date ,
                    balance=  balance ,
                    transaction_type="Credit" ,
                    status= Journal.Status.FREIGHT_IN.value,
                    purchase_inventory = instance.purchase_inventory, 
                    comment=f"freight in cost {instance.inventory}")




def purchase_inventory_update(sender, instance , created,  **kwargs):
    """
    Update this row after we purchase item and know their cost and quantity

    instance: InventoryPrice
    """
    purchase_inventory = instance.purchase_inventory

    purchase_inventory.total_purchases =  purchase_inventory.check_total_amount()
    purchase_inventory.net_purchases = purchase_inventory.check_net_purchase()
    purchase_inventory.total_amount_paid = purchase_inventory.check_total_amount_paid()
    purchase_inventory.status = 0 if purchase_inventory.check_status() =="UNPAID" else 1
    # self.due_date = self.check_due_date()
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