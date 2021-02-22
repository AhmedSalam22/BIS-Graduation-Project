from sole_proprietorship.models import Journal

def inventory_price_journal_delete(sender, instance, **kwargs):
    """Delete journal transaction related to inventory price"""
    Journal.objects.filter(
            Q(inventory_price=instance) & Q(status=Journal.Status.PURCHASE_INVENTORY.value) 
            ).delete()


def purchase_return_journal_save(sender, instance, *args, **kwargs):
    """
    Journal transaxtion related to purchase return
        A/P or CASH Debit by xxx
        Inventory Credit by     xxx
    """
    inventory_return = instance
    owner = inventory_return.inventory_price.inventory.owner
    date = inventory_return.date
    balance = inventory_return.num_returned * inventory_return.inventory_price.cost_per_unit
    transaction1 = Journal(owner=owner,
            account = inventory_return.inventory_price.inventory.general_ledeger_account,
            date = date ,
            balance= balance,
            transaction_type="Credit" , 
            comment=f"return inventory",
            statuts=Journal.Status.PURCHASE_RETURN.value
            )
    transaction1.save()
    transaction2 = Journal(owner=owner,
                account = inventory_return.inventory_price.purchase_inventory.term.general_ledeger_account,
                date = date ,
                balance=  balance ,
                transaction_type="Debit" , 
                comment=f"return {inventory_return.num_returned} from {inventory_return.inventory_price.inventory} to {inventory_return.inventory_price.purchase_inventory.supplier}",
                statuts=Journal.Status.PURCHASE_RETURN.value

                )
    transaction2.save()


def freight_in_cost():
    pass
