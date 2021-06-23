from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from sole_proprietorship.managers import TransactionManager, AccountManager

# Create your models here.
class Accounts(models.Model):
    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        constraints = [
            models.UniqueConstraint(fields=['account', 'owner'], name='unique_account')
        ]
    # account , Type , Normal Balance 
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.CharField(max_length = 250)
    normal_balance = models.CharField(
        max_length=7,
        choices= [ 
            ("Debit" , "Debit") , 
            ("Credit" , "Credit")
        ],
        default= "Debit",
    )
    account_type = models.CharField(
        max_length = 50, 
        choices = [
            ("Assest" , "Assest"),
            ("Investment" , "Investment"),
            ("liabilities" , "liabilities"),
            ("Revenue" , "Revenue"),
            ("Expenses" , "Expenses"),
            ("Drawings", "Drawings")
  
        ] , 
        default = "Assest"
    )

    objects = models.Manager() # The default manager.
    my_objects = AccountManager()

    def __str__(self):
        return self.account

class Transaction(models.Model):
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['num', 'owner'], name='unique_transaction')
        ]

    class Status(models.IntegerChoices):
        PURCHASE_INVENTORY = 1, _("Purchase Inventory")
        PURCHASE_RETURN = 2, _("Purchase return")
        PURCHASE_ALLOWANCE = 3, _("Purchase Allowance")
        FREIGHT_IN = 4, _("Freight in")
    
    @classmethod
    def num_of_transaction(cls, owner):
        return cls.objects.filter(owner=owner).count()

    @classmethod
    def last_transaction_num(cls, owner):
        query = Transaction.objects.filter(owner=owner).aggregate(models.Max('num'))
        if query['num__max'] != None:
            return query['num__max']
        return 0

    def set_num(self):
        """
        if updated keep transaction num else create new transaction num
        """
        if self.num:
            return self.num
        else:
            return Transaction.last_transaction_num(owner=self.owner) + 1

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    num = models.IntegerField()
    date = models.DateField()
    comment = models.CharField(max_length=2500 , null= True , blank=True )

  
    purchase_inventory = models.ForeignKey('inventory.PurchaseInventory', null=True, blank=True, on_delete=models.CASCADE)
    inventory_price = models.ForeignKey('inventory.InventoryPrice', null=True , blank=True, on_delete=models.CASCADE)
    inventory_return = models.ForeignKey('inventory.InventoryReturn' , null=True, blank=True, on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices , null=True, blank=True)

    objects = models.Manager() # The default manager.
    my_objects = TransactionManager()


    def save(self, *args, **kwargs):
        self.num = self.set_num()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Transaction Num:{self.num}, owner={self.owner}'


class Journal(models.Model):
    class Status(models.IntegerChoices):
        PURCHASE_INVENTORY = 1, _("Purchase Inventory")
        PURCHASE_RETURN = 2, _("Purchase return")
        PURCHASE_ALLOWANCE = 3, _("Purchase Allowance")
        FREIGHT_IN = 4, _("Freight in")

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE)

    date = models.DateField(null=True, blank=True)
    balance = models.FloatField()
    transaction_type = models.CharField(
        max_length=7,
        choices= [ 
            ("Debit" , "Debit") , 
            ("Credit" , "Credit")
        ],
        default= "Debit",
    )

    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.CharField(max_length=1500 , null= True , blank=True )
    purchase_inventory = models.ForeignKey('inventory.PurchaseInventory', null=True , on_delete=models.CASCADE)
    inventory_price = models.ForeignKey('inventory.InventoryPrice', null=True , on_delete=models.CASCADE)
    inventory_return = models.ForeignKey('inventory.InventoryReturn' , null=True  , on_delete=models.CASCADE)
    status = models.IntegerField(choices=Status.choices , null=True)
 
    def __str__(self):
        return f"{self.account}"


class ReportingPeriodConfig(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name= "fs_reporting_period",
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.owner}: from {self.start_date} to {self.end_date}"
    