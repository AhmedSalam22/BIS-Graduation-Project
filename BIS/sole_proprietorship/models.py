from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from sole_proprietorship.managers import TransactionManager, AccountManager, FinancialAnalysis
from inventory.helper import Helper
from django.db.models import Q 
from datetime import timedelta

class TransactionSignal:
    def PurchaseInventory(self, sender, instance , created,  **kwargs):
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
            Transaction.objects.filter(
                Q(inventory_price=inventory_price) & Q(status=Transaction.Status.PURCHASE_INVENTORY.value) 
                ).delete()
        
        transaction = Transaction.objects.create(
            date = purchase_inventory.purchase_date ,
            purchase_inventory = purchase_inventory,
            inventory_price = inventory_price,
            status=Transaction.Status.PURCHASE_INVENTORY.value,
            comment=f"purchase inventory {inventory_price.inventory}, number of units purchased{inventory_price.number_of_unit}")


        Journal.objects.create(
        account = inventory_price.inventory.general_ledeger_account,
        balance= inventory_price.number_of_unit *  inventory_price.cost_per_unit ,
        transaction_type="Debit",
        transaction= transaction
        
        )
        
        
        Journal.objects.create(
                    account = Helper.cash_or_accounts_payable(purchase_inventory),
                    balance= inventory_price.number_of_unit *  inventory_price.cost_per_unit ,
                    transaction_type="Credit" , 
                    transaction= transaction
                    )


        
    def PurchaseReturn(self, sender, instance , created,  **kwargs):
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
            Transaction.objects.filter(
                Q(inventory_return=instance) & Q(status=Transaction.Status.PURCHASE_RETURN.value) 
            ).delete()

        transaction = Transaction.objects.create(
            date = date ,
            inventory_return = instance,
            status=Transaction.Status.PURCHASE_RETURN.value,
            comment=f"return {instance.num_returned} from {instance.inventory_price.inventory} to {instance.inventory_price.purchase_inventory.supplier}"
        )
        Journal.objects.create(
                    account = Helper.cash_or_accounts_payable(instance.inventory_price.purchase_inventory),
                    balance=  balance ,
                    transaction_type="Debit" , 
                    transaction = transaction 
                    )

        Journal.objects.create(
                account = instance.inventory_price.inventory.general_ledeger_account,
                balance= balance,
                transaction_type="Credit" ,
                transaction = transaction 
              
        )
        


    

    def freight_in_cost(self, sender, instance , created,  **kwargs):
        """
        - record journal transaction if there is freight cost due to the purchase process
        - fright-in charge will charge of first inventory form in formset

        instance: InventoryPrice
        """
        owner = instance.purchase_inventory.owner
        date = instance.purchase_inventory.purchase_date
        balance = instance.purchase_inventory.frieght_in

        exists = Transaction.objects.filter(
            Q(purchase_inventory = instance.purchase_inventory) & Q(status=Transaction.Status.FREIGHT_IN.value) 
            ).exists()

        if not exists and balance != 0:
            transaction = Transaction.objects.create(
                date = date,
                comment=f"freight in cost {instance.inventory}",
                status= Transaction.Status.FREIGHT_IN.value,
                purchase_inventory = instance.purchase_inventory, 

            )
            Journal.objects.create(
                    account = instance.inventory.general_ledeger_account,
                    balance= balance ,
                    transaction_type="Debit" , 
                    transaction= transaction
                    )
            Journal.objects.create(
                        account = instance.purchase_inventory.term.freight_in_account,
                        balance=  balance ,
                        transaction_type="Credit" ,
                        transaction= transaction
                        )




    def pay_invoice(self, sender, instance, create, **kwargs):
        """
        Journal Entry to record paid Invoice
        A/p Debit by  xxxx
            Cash Credit by xxxxx
            Inventory[dicount] credit by xxxx
        instance:PayInvoice
        """
        
        if not create:
            Transaction.objects.filter(
                Q(pay_invoice=instance) & Q(status=Transaction.Status.PAY_INVOICE.value) 
            ).delete()

        transaction = Transaction.objects.create(
            date = instance.date ,
            pay_invoice = instance,
            status=Transaction.Status.PAY_INVOICE.value,
            comment=f"PAY invoice"
        )

        dicount_percentage = instance.purchase_inventory.term.discount_percentage
        if instance.purchase_inventory.payinvoice_set.count() == 1 and instance.purchase_inventory.term.discount_percentage > 0 and instance.date <= (instance.purchase_inventory.purchase_date.date() + timedelta(instance.purchase_inventory.term.discount_in_days)):
            total_amount = instance.amount_paid/ ( (100 - dicount_percentage) / 100)
            Journal.objects.create(
                                account = instance.purchase_inventory.term.accounts_payable,
                                balance=  total_amount ,
                                transaction_type="Debit" ,
                                transaction= transaction
                                ) 
            #Cash credit by amount Paid
            Journal.objects.create(
                    account = instance.purchase_inventory.term.cash_account,
                    balance=  instance.amount_paid ,
                    transaction_type="Credit" ,
                    transaction= transaction
                    ) 
            #Discount
            Journal.objects.create(
                account = instance.purchase_inventory.inventoryprice_set.first().inventory.general_ledeger_account,
                balance=  total_amount * (dicount_percentage / 100) ,
                transaction_type="Credit" ,
                transaction= transaction
                ) 
        else:
            Journal.objects.create(
                        account = instance.purchase_inventory.term.accounts_payable,
                        balance=  instance.amount_paid ,
                        transaction_type="Debit" ,
                        transaction= transaction
                        )
            Journal.objects.create(
                    account = instance.purchase_inventory.term.cash_account,
                    balance=  instance.amount_paid ,
                    transaction_type="Credit" ,
                    transaction= transaction
                    ) 
    
    
    def purchase_allowance(self, sender, instance, created, **kwargs):
        """
        Journal Entry to record Purchase Allowance
        A/p (cash) Debit by  xxxx
            Inventory Credit by xxxxx

        instance: InventoryAllowance
        """
        
        if not created:
            Transaction.objects.filter(
                Q(purchase_allowance=instance) & Q(status=Transaction.Status.PURCHASE_ALLOWANCE.value) 
            ).delete()

        transaction = Transaction.objects.create(
            date = instance.date ,
            purchase_allowance = instance,
            status=Transaction.Status.PURCHASE_ALLOWANCE.value,
            comment=f"Purcase Allowance"
        )

        Journal.objects.create(
                account = Helper.cash_or_accounts_payable(instance.purchase_inventory),
                balance= instance.amount,
                transaction_type="Debit" ,
                transaction = transaction 
              
                )
        Journal.objects.create(
                account = instance.inventory_price.inventory.general_ledeger_account,
                balance= instance.amount,
                transaction_type="Credit" ,
                transaction = transaction 
              
                )
        
    def sale(self, sender, instance, created, **kwargs):
        """
        Journal Entry to record Sale
        A/R or Cash Debit by xxx
            Sales Revenue Credit by xxx

        Journal Entry to record Cost of Goods Sold
        COGS Debit by xxx
            Inventory Credit by xxx

        instance:Sold_Item
        """

        if not created:
            Transaction.objects.filter(
                Q(sold_item=instance) & Q(status=Transaction.Status.SALES.value) 
            ).delete()


        transaction = Transaction.objects.create(
            date = instance.sale.sales_date ,
            sold_item = instance,
            status=Transaction.Status.SALES.value,
            comment=f"Sales Item"
        )

       
                       
        Journal.objects.create(
                account = instance.sale.ARorCash(),
                balance=  instance.sale_price * instance.quantity ,
                transaction_type="Debit" ,
                transaction= transaction
                ) 

        Journal.objects.create(
                    account = instance.sale.term.sales_revenue,
                    balance=  instance.sale_price * instance.quantity ,
                    transaction_type="Credit" ,
                    transaction= transaction
                    ) 

        Journal.objects.create(
                        account = instance.sale.term.COGS,
                        balance=  instance.item.cost_per_unit * instance.quantity ,
                        transaction_type="Debit" ,
                        transaction= transaction
        ) 

        Journal.objects.create(
                    account = instance.item.inventory.general_ledeger_account,
                    balance=  instance.item.cost_per_unit * instance.quantity ,
                    transaction_type="Credit" ,
                    transaction= transaction
        ) 



    def sale_return(self, sender, instance, created, **kwargs):
        """
         Journal entry to record sales return
         Sales Return and Allowance Debit by xxxx
            Cash or A/R Credit by xxxx

        Inventory Debit by xxx
            COGS Credit by xxx

        instance:SalesReturn
        """
        if not created:
            Transaction.objects.filter(
                Q(sales_return=instance) & Q(status=Transaction.Status.SALES_RETURN.value) 
            ).delete()

        transaction = Transaction.objects.create(
            date = instance.date ,
            sales_return = instance,
            status=Transaction.Status.SALES_RETURN.value,
            comment=f"Sales Return"
        )  

        Journal.objects.create(
            account = instance.sale.term.sales_return,
            balance=  instance.num_returned * instance.sold_item.sale_price ,
            transaction_type="Debit" ,
            transaction= transaction
        ) 

        Journal.objects.create(
            account = instance.sale.ARorCash(),
            balance=  instance.num_returned * instance.sold_item.sale_price ,
            transaction_type="Credit" ,
            transaction= transaction
        ) 

        Journal.objects.create(
            account = instance.sold_item.item.inventory.general_ledeger_account,
            balance=  instance.num_returned * instance.sold_item.item.cost_per_unit ,
            transaction_type="Debit" ,
            transaction= transaction
        ) 
 
        Journal.objects.create(
            account = instance.sale.term.COGS,
            balance=  instance.num_returned * instance.sold_item.item.cost_per_unit ,
            transaction_type="Credit" ,
            transaction= transaction
        ) 



    def sale_allowance(self, sender, instance, created, **kwargs):
        """
        Journal Entry to record Sales Allowance
            Sales Allowance Debit by xxxx
                Cash or A/R Credit by xxx
        instance:SalesAllowance
        """
        if not created:
            Transaction.objects.filter(
                Q(sales_allowance=instance) & Q(status=Transaction.Status.SALES_ALLOWANCE.value) 
            ).delete()


        transaction = Transaction.objects.create(
            date = instance.date ,
            sales_allowance = instance,
            status=Transaction.Status.SALES_ALLOWANCE.value,
            comment=f"Sales Allowance"
        )  

        Journal.objects.create(
            account = instance.sales.term.sales_allowance,
            balance=  instance.amount ,
            transaction_type="Debit" ,
            transaction= transaction
        ) 

        Journal.objects.create(
            account = instance.sales.ARorCash(),
            balance=  instance.amount ,
            transaction_type="Credit" ,
            transaction= transaction
        ) 


    def received_payment(self, sender, instance, created, **kwargs):
        """
        Journal Entry to record Sales Discount
            Cash Debit by xxxx
            [Sales Discount   Debit by xxxx]
                Accounts Receivable credit by xxx
        instance:SalesPayment
        """
        if not created:
            Transaction.objects.filter(
                Q(received_payment=instance) & Q(status=Transaction.Status.RECEIVED_PAYMENT.value) 
            ).delete()

        transaction = Transaction.objects.create(
            date = instance.date ,
            received_payment = instance,
            status=Transaction.Status.RECEIVED_PAYMENT.value,
            comment=f"Sales Payment"
        )

        if instance.first_payment and instance.discount() and instance.amount == instance.amount_if_there_discount():
            Journal.objects.create(
                account = instance.sales.term.cash_account,
                balance=  instance.amount_if_there_discount() ,
                transaction_type="Debit" ,
                transaction= transaction
            )
            Journal.objects.create(
                account = instance.sales.term.sales_discount,
                balance=  (instance.sales.net_sales - instance.instance.amount_if_there_discount()) ,
                transaction_type="Debit" ,
                transaction= transaction
            )  
            Journal.objects.create(
                account = instance.sales.term.accounts_receivable,
                balance=  instance.sales.net_sales,
                transaction_type="Credit" ,
                transaction= transaction
            )  
        else:
            Journal.objects.create(
                account = instance.sales.term.cash_account,
                balance=  instance.amount ,
                transaction_type="Debit" ,
                transaction= transaction
            )
            
            Journal.objects.create(
                account = instance.sales.term.accounts_receivable,
                balance=  instance.amount,
                transaction_type="Credit" ,
                transaction= transaction
            )  


# Create your models here.
class Accounts(models.Model):
    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        constraints = [
            models.UniqueConstraint(fields=['account', 'owner'], name='unique_account')
        ]
        indexes = [
            models.Index(fields=['account', 'owner'], name='account_idx'),
            models.Index(fields=['owner'], name='acc_owner_idx'),

        ]

      
    CLASSIFICATION_CHOICES = [
        ('Current Assets', (
                ('Current Assets', 'Current Assets'),
                ('Cash', 'Cash'),
                ('Marketable securities or short-term investments', 'Marketable securities or short-term investments'),
                ('Receivable', 'Receivable'),
                ('Inventory', 'Inventory'),
                ('prepaids', 'prepaids')

            )
        ),
        ('Property, plant, and equipment', 'Property, plant, and equipment'),
        ('Intangible assets', 'Intangible assets'),
        ('Long-term investments', 'Long-term investments'),
        ('Contra', (
            ('Contra Assets', 'Contra Assets'),
            ('Allowance for Doubtful Accounts', 'Allowance for Doubtful Accounts'),
            ('Revenue-Contra', 'Revenue-Contra')

            )
        ),
        ('Liabilities', (
            ('Current liabilities', 'Current liabilities'),
            ('Long-term liabilities', 'Long-term liabilities')
        )),
        ('Revenue', (
                ('Sales', 'Sales'),
                ('Other Revenue and gains', 'Other Revenue and gains')
            )
        ),
        ('Expenses', (
                ('COGS', 'Cost of Goods Sold'),
                ('Operating Expense', 'Operating Expense'),
                ('Other Expenses And Losses', 'Other Expenses And Losses')
            )
        )
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
            ("Assest" , "Assets"),
            ("Investment" , "Investment"),
            ("liabilities" , "Liabilities"),
            ("Revenue" , "Revenue"),
            ("Expenses" , "Expenses"),
            ("Drawings", "Drawings")
  
        ]     
    )
    
    classification = models.CharField(
        max_length=90,
        choices=CLASSIFICATION_CHOICES,
        null= True,
        blank= True
    )


    objects = models.Manager() # The default manager.
    my_objects = AccountManager()
    financial = FinancialAnalysis()

    def __str__(self):
        return self.account

class Transaction(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['date'], name='date_idx'),
        ]

    class Status(models.IntegerChoices):
        PURCHASE_INVENTORY = 1, _("Purchase Inventory")
        PURCHASE_RETURN = 2, _("Purchase return")
        PURCHASE_ALLOWANCE = 3, _("Purchase Allowance")
        FREIGHT_IN = 4, _("Freight in")
        PAY_INVOICE = 5, _("Pay Invoice")
        SALES = 6, _('Sales')
        SALES_RETURN = 7, _('Sales Return')
        SALES_ALLOWANCE = 8, _('Sales Allowance')
        RECEIVED_PAYMENT = 9, _('Received Payment')
    
    @classmethod
    def num_of_transaction(cls, owner):
        return cls.objects.filter(journal__account__owner=owner).distinct().count()
    
    date = models.DateField()
    comment = models.CharField(max_length=2500 , null= True , blank=True )

    # we will change this in future uing JSONFIELD
    purchase_inventory = models.ForeignKey('inventory.PurchaseInventory', null=True, blank=True, on_delete=models.CASCADE)
    inventory_price = models.ForeignKey('inventory.InventoryPrice', null=True , blank=True, on_delete=models.CASCADE)
    inventory_return = models.ForeignKey('inventory.InventoryReturn' , null=True, blank=True, on_delete=models.CASCADE)
    pay_invoice = models.ForeignKey('inventory.PayInvoice' , null=True, blank=True, on_delete=models.CASCADE)  
    purchase_allowance = models.ForeignKey('inventory.InventoryAllowance', null=True, blank=True, on_delete= models.CASCADE)
    # sale = models.ForeignKey('inventory.Sale', null=True, blank=True, on_delete=models.CASCADE)
    sold_item = models.ForeignKey('inventory.Sold_Item', null=True, blank=True, on_delete=models.CASCADE)
    sales_return = models.ForeignKey('inventory.SalesReturn', null=True, blank=True, on_delete= models.CASCADE)
    sales_allowance = models.ForeignKey('inventory.SalesAllowance', null=True, blank=True, on_delete= models.CASCADE)
    received_payment = models.ForeignKey('inventory.SalesPayment', null=True, blank=True, on_delete= models.CASCADE)
    status = models.IntegerField(choices=Status.choices , null=True, blank=True)

    objects = models.Manager() # The defaul t manager.
    my_objects = TransactionManager()

    signal = TransactionSignal()    

    def __str__(self):
        return f'Transaction Num:{self.pk}'


class Journal(models.Model):
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE)
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
    company_name = models.CharField(max_length=300, null=True, blank=True)

    def __str__(self):
        return f"{self.owner}: from {self.start_date} to {self.end_date}"
    