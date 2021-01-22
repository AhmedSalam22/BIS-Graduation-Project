from django.db import models
from sole_proprietorship.models import Accounts
from django.contrib.auth import get_user_model
from suppliers.models import Supplier
from django.utils.translation import gettext as _
from  django.core.validators import MaxValueValidator
from django.utils import timezone
from django.db.models import Sum , ExpressionWrapper , F , FloatField , Max , Min , Avg , StdDev
import calendar
from django.core.exceptions import ValidationError
# Create your models here.
class PaymentSalesTerm(models.Model):
    class Term(models.IntegerChoices):
        CASH = 0 , _("Pay CASH")
        ON_DEMAND = 1 , _("Cash On Demand")
        DAYS = 2, _("Due in number of days")
        END_OF_MONTH = 3,_("Due at the end of month")
        NEXT_MONTH = 4,_("Due on the next Month")
        OTHER = 5, _("let me specify the due date DD-MM-YYY")


    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    config = models.CharField(
        max_length=100,
        help_text="Specify name for this setting"
        )
    terms = models.IntegerField(choices=Term.choices , default=Term.CASH , blank=False)
    num_of_days_due = models.PositiveSmallIntegerField(
        help_text="in case of you want to specify number of days due"
    )
    discount_in_days = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(32)] ,
        null = True,
        blank = True
    )
    discount_percentage = models.FloatField(
        help_text="Enter discount like this 5%>>will be  5 not 0.05",
  
    )
    general_ledeger_account = models.ForeignKey(Accounts,on_delete=models.CASCADE)

    def __str__(self):
        return self.config

class Inventory(models.Model):
    """
    Create Inventory table in db.
    we will use this table to save inventory item and related account inventory for this item 
    i can use just one inventrory account for all item in inventory but i created one - to many relation 
    in order to make it's dynamic in other meaning we can have many inventory account so there is FK
    """
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    item_name = models.CharField(max_length=250)
    description = models.TextField(
        null= True,
        blank= True
    )
    general_ledeger_account = models.ForeignKey(Accounts,on_delete=models.CASCADE)

    def __str__(self):
        return self.item_name


def inventory_imag_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'inventory/inventory_imgs/user_{0}/{3}/{2}{1}'.format(instance.inventory.owner,
     filename ,
     timezone.now() , 
     instance.inventory.item_name
      )

class InventoryImag(models.Model):
    """
    this is table hold images for the inventory item each inventory can has many image
    """
    class Meta:
        verbose_name = 'Inventory Image'
        verbose_name_plural = 'Inventory Images'

    inventory  = models.ForeignKey(Inventory , on_delete=models.CASCADE , related_name="imgs" )
    img = models.ImageField(upload_to=inventory_imag_directory_path,
                                null=True,
                                blank=True,
                                editable=True,
                                help_text="Inventory image")
    
    def __str__(self):
        return f"img:{self.inventory.item_name}"



class PurchaseManager(models.Manager):
    def avg_cost_per_unit(self , owner):
        """
        avg cost per unit
        """
        data = self.filter(owner=owner).aggregate(Avg("inventoryprice__cost_per_unit"))
        return data.get("inventoryprice__cost_per_unit__avg" , 0)

    def std_cost_per_unit(self, owner):
        """
        return the stander deviation (change upward ow donward) for cost per unit
        """
        query = self.filter(owner=owner).aggregate(StdDev("inventoryprice__cost_per_unit"))
        return query.get("inventoryprice__cost_per_unit__stddev" , 0)

    def max_cost_per_unit(self , owner):
        query = self.filter(owner=owner).aggregate(Max("inventoryprice__cost_per_unit"))
        return query.get("PurchaseInventory.objects.filter(owner=2" , 0)

    def min_cost_per_unit(self , owner):
        query = self.filter(owner=owner).aggregate(Min("inventoryprice__cost_per_unit"))
        return query.get("inventoryprice__cost_per_unit__min" , 0)

    def total_units_purchased(self , owner):
        """
        sum of of total unit purchased we don't take into account(returned cost this will be different method)
        args: 
            owner
        return 
            the sum of unit's purchases 
        """
        data = self.filter(owner=owner).aggregate(Sum("inventoryprice__number_of_unit"))
        return data.get("inventoryprice__number_of_unit__sum" , 0)

    def total_purchases_amount(self , owner):
        """
         sum of total purchases amount (freight in or returned purchased not included)
        """
        query = self.filter(owner=owner).annotate(
                    total_cost=ExpressionWrapper(
                        F("inventoryprice__cost_per_unit")*F("inventoryprice__number_of_unit"), output_field=FloatField()
                        )).aggregate(Sum("total_cost"))
        return  query["total_cost__sum"] if query["total_cost__sum"] != None else 0

    def total_units_returned(self , owner):
        query = self.filter(owner=owner).aggregate(Sum("inventoryprice__inventoryreturn__num_returned"))
        return query.get("inventoryprice__inventoryreturn__num_returned__sum" , 0)


    def total_cost_of_units_returned(self , owner):
        query = self.filter(owner=owner).annotate(
                        total_cost=ExpressionWrapper(
                        F("inventoryprice__cost_per_unit")*F("inventoryprice__inventoryreturn__num_returned"), output_field=FloatField()
                        )).aggregate(Sum("total_cost"))
        return query["total_cost__sum"] if query["total_cost__sum"] != None else 0

    def net_purchases(self , owner):
        return PurchaseManager.total_purchases_amount(self , owner) - PurchaseManager.total_cost_of_units_returned(self ,owner)

    def total_amount_paid(self , owner):
        # this one for PAID invoice already on Cash
        PAID = [obj.net_purchase for obj in self.filter(owner=owner) if obj.check_status() == "PAID"]
        # this query of unpaid invoice anfd then we pay it partuaily or full the amount
        query = self.filter(owner=owner).aggregate(Sum("payinvoice__amount_paid"))
        return (query["payinvoice__amount_paid__sum"] if query["payinvoice__amount_paid__sum"] != None else 0) + sum(PAID)

    def total_amount_unpaid(self, owner):
        return PurchaseManager.net_purchases(self ,owner) - PurchaseManager.total_amount_paid(self ,owner)

    def unique_supplier(self, owner):
        return set([obj.supplier for obj in self.filter(owner=owner)])

    def group_by_supplier(self , owner):
        data = {
            "Supplier": [] , 
            "net_pruchases": [] ,
            "total_amount_unpaid": [] ,
            "total_amount_paid" : [] , 
            "total_cost_of_units_returned": [] ,
            "total_units_returned": [] ,
            "total_purchases_amount" : [] ,
            "total_units_purchased": []

        }

        for supplier in self.unique_supplier(owner):
            data["Supplier"].append(supplier.full_name)
            query = PurchaseInventory.objects.filter(owner=owner , supplier = supplier)
            data["net_pruchases"].append(PurchaseManager.net_purchases(query , owner))
            data["total_purchases_amount"].append(PurchaseManager.total_purchases_amount(query ,  owner))
            data["total_amount_unpaid"].append(PurchaseManager.total_amount_unpaid(query , owner))
            data["total_amount_paid"].append(PurchaseManager.total_amount_paid(query , owner))
            data["total_cost_of_units_returned"].append(PurchaseManager.total_cost_of_units_returned(query , owner))
            data["total_units_purchased"].append(PurchaseManager.total_units_purchased(query , owner))
            data["total_units_returned"].append(PurchaseManager.total_units_returned(query , owner))

        return data


    
        



class PurchaseInventory(models.Model):
    """
    Note freight in cost which inccure when you purchase your inventory will charge only on the first
    form inventory in formset
    """
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    # a unique identifyer for youe purchase tansaction
    num = models.IntegerField()
    purchase_date = models.DateTimeField()
    due_date = models.DateField(
        help_text="optional if you want to specify it by yourself",
        null = True ,
        blank = True,
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    term = models.ForeignKey(PaymentSalesTerm, on_delete=models.CASCADE)
    frieght_in = models.FloatField(default=0)

    objects = models.Manager() # the default_managers
    purchases = PurchaseManager()

    def check_status(self):
        """
        Check if this invoice PAID or UNPAID
        """
        if self.term.terms == 0 or (self.net_purchase == self.total_amount_paid):
            return "PAID"
        else:
            return  "UNPAID"

    
    def check_due_date(self):
        """
        retrun due date if user don't specify it's directly and used terms instead
        """
        if self.due_date:
            return self.due_date
        else:
            # Due in number of days
            if self.term.terms == PaymentSalesTerm.Term.DAYS.value:
                return self.purchase_date + timezone.timedelta(days=self.term.num_of_days_due)
            elif self.term.terms == PaymentSalesTerm.Term.END_OF_MONTH.value:
                return timezone.datetime(
                    year = self.purchase_date.year , 
                    month = self.purchase_date.month , 
                    day = calendar.monthrange(
                            year= self.purchase_date.year ,
                            month = self.purchase_date.month
                    )[1]
                )
            # we mean by next month ex purchase date was feb-02-2021 so due date march-02-2021
            elif self.term.terms == PaymentSalesTerm.Term.NEXT_MONTH.value:
                if self.purchase_date.month == 12:
                    return timezone.datetime(
                            year = self.purchase_date.year + 1 , 
                            month = 1 , 
                            day = self.purchase_date.day
                )
                else:
                    return timezone.datetime(
                        year = self.purchase_date.year , 
                        month = self.purchase_date.month + 1, 
                        day = self.purchase_date.day
                    )





    @property
    def num_cost_of_returned_inventory(self) -> tuple:
        """
        return a tuble of  total number of returned and it's cost
        # take into account if we return inventory so we accumulate this cost
        # for now we do it on reqular python insted of db for simplicity by in 
        # future should do in database level for speed and performance
        """
        cost_of_returned_inventory = 0
        total_returned = 0
        for inventory_price in self.inventoryprice_set.all():
            cost_per_unit = inventory_price.cost_per_unit
            for inventory_return in inventory_price.inventoryreturn_set.all():
                total_cost = inventory_return.num_returned * cost_per_unit
                total_returned += inventory_return.num_returned
                cost_of_returned_inventory += total_cost
        return total_returned , cost_of_returned_inventory

    @property
    def total_amount(self) -> float:
        """amount of purchase whether on account or paid cash"""
        # reurn dict for total amount of purchases
        query = self.inventoryprice_set.annotate(
                    total_cost=ExpressionWrapper(
                        F("cost_per_unit")*F("number_of_unit"), output_field=FloatField()
                        )).aggregate(total_amount=Sum("total_cost"))

        
        return query.get("total_amount" , 0)

    @property
    def net_purchase(self):
        """
        return amount of purchase take into our account if we return some inventory
        """
        return self.total_amount - self.num_cost_of_returned_inventory[1]

    @property
    def total_amount_paid(self):
        """
        return  total amount paid for specific invoice
        """
        query = self.payinvoice_set.aggregate(Sum("amount_paid"))["amount_paid__sum"]
        if query == None:
            return 0
        return query
 
    def __str__(self):
        return f"invoice number:{self.pk}"
    
    # we will add in the future the address for the supplier and the ship address

class PayInvoice(models.Model):
    purchase_inventory = models.ForeignKey(PurchaseInventory , on_delete=models.CASCADE)
    amount_paid = models.FloatField()

            

    def clean(self):
        amount_paid = self.purchase_inventory.total_amount_paid
        invoice_cost = self.purchase_inventory.net_purchase - amount_paid
        if self.amount_paid > invoice_cost:
            raise ValidationError({
        "amount_paid":ValidationError(_("Paid amount can't be greater than invoice cost") , code="invaild") , 
        })
       

    def __str__(self):
        return f"Pay {self.purchase_inventory}"
    

class InventoryPrice(models.Model):
    """
    Create InventoryPrice table in db.
    as you know each inventory can has multiple price so there are accounting method such as FIFO,LIFO,Moving Average
    in order to solve this proble there are one-To-Many Relationship (Inventort >> InventoryPtie)
    so when i record transaction:

    Model Inventory: 
        Product X
    
    Model InventoryPrice:
        purchase one time on 01-jan-2021 , 10 units with price 10 per unit so total cost = 100
        purchase second time the same product on 01-mar-2021, 10 units with price 12 so total cost 120
    
    Overview:
        Total cost now = 100 + 120 = 220 
        Number of unit = 20

    you will have the choice to sell the inventory who cost you 10 first or the inventory who cost you 12 first
    by this way we will avoide the headache of FIFO ,LIFO when we sell the inventory to the customer so you have
    the choice and keep our Transaction clean when we track the cost
    """
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    cost_per_unit = models.FloatField()
    number_of_unit = models.PositiveIntegerField()
    purchase_inventory = models.ForeignKey(PurchaseInventory, on_delete=models.CASCADE)

    @property
    def total_cost(self):
        return self.cost_per_unit * self.number_of_unit

    def __str__(self):
        return f"{self.inventory.item_name}:{self.cost_per_unit}/unit"


class InventoryReturn(models.Model):
    """
        Purchase Return Model
    """
    inventory_price = models.ForeignKey(InventoryPrice, on_delete=models.CASCADE)
    date = models.DateField()
    num_returned = models.PositiveIntegerField()


    def __str__(self):
        return f"return {self.num_returned} of {self.inventory_price.inventory.item_name}"