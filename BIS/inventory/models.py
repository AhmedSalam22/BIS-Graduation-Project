from django.db import models
from django.contrib.auth import get_user_model
from suppliers.models import Supplier
from django.utils.translation import gettext as _
from  django.core.validators import MaxValueValidator
from django.utils import timezone
from django.db.models import (Sum, ExpressionWrapper, F, FloatField, Max, Min, Avg, StdDev, Count, Q, Func,
                                DateTimeField, Case, When, Value
                             )
import calendar
from django.core.exceptions import ValidationError
from django.db import connection
import datetime
from django.utils import timezone 
from datetime import timedelta
from django.db.models.functions import Coalesce, Concat
from django.utils.functional import cached_property
from ckeditor.fields import RichTextField



def test():
    PurchaseInventory.objects.annotate(
        total_amount_unpaid=(F("net_purchases")- F("total_amount_paid")),
        due=ExpressionWrapper( 
            Case(
                When(
                due_date__gt = now() , then=Value("Over due")
                ),
                When(
                due_date__lte = now() , then=Value("Not Due Yet")
                ),
            ),
            output_field = models.CharField(max_length=20)
        )

    ).filter(
        status=PurchaseInventory.Status.UNPAID.value
    )


# Create your models here.
class DueDateMixin:
    def check_due_date(self):
        """
        retrun due date if user don't specify it's directly and used terms instead
        """
        if hasattr(self, 'purchase_date'):
            issue_date = self.purchase_date
        else:
            issue_date = self.sales_date

        if self.due_date:
            return self.due_date
        else:
            # Due in number of days
            if self.term.terms == PaymentSalesTerm.Term.DAYS.value:
                return issue_date + timezone.timedelta(days=self.term.num_of_days_due)
            elif self.term.terms == PaymentSalesTerm.Term.END_OF_MONTH.value:
                return timezone.datetime(
                    year = issue_date.year , 
                    month = issue_date.month , 
                    day = calendar.monthrange(
                            year= issue_date.year ,
                            month = issue_date.month
                    )[1]
                )
            # we mean by next month ex purchase date was feb-02-2021 so due date march-02-2021
            elif self.term.terms == PaymentSalesTerm.Term.NEXT_MONTH.value:
                if issue_date.month == 12:
                    return timezone.datetime(
                            year = issue_date.year + 1 , 
                            month = 1 , 
                            day = issue_date.day
                )
                else:
                    return timezone.datetime(
                        year = issue_date.year , 
                        month = issue_date.month + 1, 
                        day = issue_date.day
                    )
    
   



class PaymentSalesTerm(models.Model):
    class Term(models.IntegerChoices):
        CASH = 0 , _("Pay CASH")
        ON_DEMAND = 1 , _("Cash On Demand")
        DAYS = 2, _("Due in number of days")
        END_OF_MONTH = 3,_("Due at the end of month")
        NEXT_MONTH = 4,_("Due on the next Month")
        OTHER = 5, _("let me specify the due date DD-MM-YYY")

    class PAY_METHOD(models.IntegerChoices):
        CASH = 1
        ACCOUNTS_PAYABLE = 2


    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    config = models.CharField(
        max_length=100,
        help_text="Specify name for this setting"
        )
    terms = models.IntegerField(choices=Term.choices , default=Term.CASH , blank=False)
    num_of_days_due = models.PositiveSmallIntegerField(
        help_text="in case of you want to specify number of days due",
        default= 0
    )
    discount_in_days = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(32)] ,
        null = True,
        blank = True,
        default = 0
    )
    discount_percentage = models.FloatField(
        help_text="Enter discount like this 5%>>will be  5 not 0.05",
        default = 0
  
    )
    # general_ledeger_account = models.ForeignKey('sole_proprietorship.Accounts',on_delete=models.CASCADE)
    cash_account =  models.ForeignKey('sole_proprietorship.Accounts',on_delete=models.CASCADE , related_name='payment_sales_term_cash_account')
    accounts_payable =models.ForeignKey('sole_proprietorship.Accounts',on_delete=models.CASCADE , related_name='payment_sales_term_accounts_payable_account')
    freight_in_account = models.ForeignKey('sole_proprietorship.Accounts',
                                    on_delete=models.CASCADE,
                                    related_name='freight_in_account',
                                    help_text='choose A/p or Cash to determine if you paid this cost cash or not')

    freight_out_account = models.ForeignKey('sole_proprietorship.Accounts',
        on_delete= models.CASCADE,
        help_text = 'choose frieght out expense account',
        related_name = 'freight_out_account'
    )
    pay_freight_out = models.IntegerField(choices=PAY_METHOD.choices,
        help_text = 'How You will pay frieht-out?',
    )

    COGS =  models.ForeignKey('sole_proprietorship.Accounts',
    on_delete=models.CASCADE,
    help_text='Select Cost of goods sold Account',
    related_name = 'COGS'
    )

    sales_revenue = models.ForeignKey('sole_proprietorship.Accounts',
        on_delete=models.CASCADE,
        help_text='Select Sales revenue account',
        related_name = 'sales_revenue'
    )

    accounts_receivable = models.ForeignKey('sole_proprietorship.Accounts',
        on_delete=models.CASCADE,
        help_text='Select Accounts receivable account',
        related_name = 'accounts_receivable'
    )

    sales_return = models.ForeignKey('sole_proprietorship.Accounts',
        on_delete=models.CASCADE,
        help_text='Select Sales return account',
        related_name = 'sales_return'
    )

    sales_allowance = models.ForeignKey('sole_proprietorship.Accounts',
        on_delete=models.CASCADE,
        help_text='Select Sales allowance account',
        related_name = 'sales_allowance'
    )

    sales_discount = models.ForeignKey('sole_proprietorship.Accounts',
        on_delete=models.CASCADE,
        help_text='Select Sales discount account',
        related_name = 'sales_discount'
    )


  

    
    
    def __str__(self):
        return self.config

# class Category(models.Model):
#     owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
#     category = models.CharField(max_length=250)

#     def __str__(self):
#         return f'{self.category}'


class InventoryAnalysis(models.Manager):

    def inventory_analysis(self, owner):
        Inventory.objects.annotate(
            units_purchases=Coalesce(Sum('inventoryprice__number_of_unit', output_field=models.IntegerField()), Value(0)),
            units_return_from_purchases=Coalesce(Sum('inventoryprice__inventoryreturn__num_returned', output_field=models.IntegerField()), Value(0)),
            net_units_purchases = ExpressionWrapper(
                F('units_purchases') - F('units_return_from_purchases'), output_field=models.IntegerField()
                ),
            units_sold=Coalesce(Sum('inventoryprice__sold_item__quantity', output_field=models.IntegerField()), Value(0)),
            units_return_from_sales=Coalesce(Sum('inventoryprice__sold_item__salesreturn__num_returned', output_field=models.IntegerField()), Value(0)),
            net_units_sold = ExpressionWrapper(
                F('units_sold') - F('units_return_from_sales'), output_field=models.IntegerField()
            ),
            
        ).values(
            'id',
            'item_name',
            'units_purchases',
            'units_return_from_purchases',
            'net_units_purchases',
            'units_sold',
            'units_return_from_sales',
            'net_units_sold'
        )



class Inventory(models.Model):
    """
    Create Inventory table in db.
    we will use this table to save inventory item and related account inventory for this item 
    i can use just one inventrory account for all item in inventory but i created one - to many relation 
    in order to make it's dynamic in other meaning we can have many inventory account so there is FK
    """
    class Meta:
        indexes = [
            models.Index(fields=['item_name'], name='item_name_idx'),
        ]

    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    item_name = models.CharField(max_length=250)
    description = RichTextField(
        null= True,
        blank= True
    )
    
    general_ledeger_account = models.ForeignKey('sole_proprietorship.Accounts',on_delete=models.CASCADE)
    # category = models.ManyToManyField(Category, null=True, blank=True)


    def __str__(self):
        return self.item_name





def inventory_imag_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f'inventory/inventory_imgs/user_{instance.inventory.owner}/{instance.inventory.item_name}/{filename}'

class InventoryImag(models.Model):
    """
    this is table hold images for the inventory item each inventory can has many image
    """
    class Meta:
        verbose_name = 'Inventory Image'
        verbose_name_plural = 'Inventory Images'

    inventory  = models.ForeignKey(Inventory , on_delete=models.CASCADE , related_name="imgs" )
    img = models.ImageField(upload_to=inventory_imag_directory_path,
                                editable=True,
                                help_text="Inventory image")
    
    def __str__(self):
        return f"img:{self.inventory.item_name}"



class DateAdd(Func):
    """
    refrence: https://stackoverflow.com/questions/33981468/using-dateadd-in-django-filter
    Custom Func expression to add date and int fields as day addition
    Usage: models.objects.annotate(end_date=DateAdd('start_date','duration')).filter(end_date__gt=datetime.now)
    """
    arg_joiner = " + CAST("
    template = "%(expressions)s || ' days' as INTERVAL)"
    output_field = DateTimeField()


class SaleManager(models.Manager):
    def all_sales(self, owner_id):
        query = Sale.objects.filter(
            owner__id = owner_id
        ).annotate(
            total_sales= ExpressionWrapper(
                 Sum(F('sold_item__sale_price') * F('sold_item__quantity'), output_field=FloatField()) 
                , output_field= FloatField()
            ),
            sales_return_amt  = ExpressionWrapper(
                Coalesce(
                    Sum(
                        (
                            F('sold_item__sale_price') * F('salesreturn__num_returned')
                        ), output_field = FloatField()
                        ),
                    0.0
                    ),
                output_field= FloatField()
                ),  
            allowance=ExpressionWrapper(
                Coalesce(Sum('salesallowance__amount',  output_field= FloatField()), 0.0),
                output_field= FloatField()

            ),
            netsales = ExpressionWrapper(F('total_sales') - F('sales_return_amt')- F('allowance'),  output_field= FloatField()),
            total_amt_paid= Coalesce(Sum('salespayment__amount',  output_field= FloatField()), 0.0)
        
        ).annotate(
            amt_after_discount = ExpressionWrapper(
                F('netsales') * ((100- F("term__discount_percentage")) / 100),
                output_field= FloatField()
            ),
            num_payment = Count('salespayment')
        ).annotate(
            status = Case(
                When(term__terms = PaymentSalesTerm.Term.CASH.value, then=Value('PAID')),
                When(netsales = F('total_amt_paid'), then= Value('PAID')),
                When(
                    Q(total_amt_paid = F('amt_after_discount')) & Q(num_payment = 1) & Q(salespayment__date__lte = DateAdd(F('sales_date') ,(F('term__discount_in_days')))), 
                    then= Value('PAID')
                ),
                default=Value("UNPAID"),
                output_field= models.CharField(max_length=6)
            )
        ).annotate(
            total_amt_unpaid = ExpressionWrapper(F('netsales') - F('total_amt_paid'), output_field= FloatField()),
            customer_name=Concat(F('customer__first_name'), Value(' '), F('customer__middle_name'), Value(' '), F('customer__last_name'))
          
        )
        return query

class PurchaseManager(models.Manager):
    def purchases_analysis(self , query):
        data = PurchaseInventory.objects.filter(query).aggregate(
            total_amount_paid=Sum("total_amount_paid"), 
            count=Count("pk") , 
            num_returend=Sum("num_returend")  ,
            cost_returned=Sum("cost_returned") ,
            total_purchases=Sum("total_purchases")  , 
            net_purchases=Sum("net_purchases")
             )
        data["unpaid_count"] = PurchaseInventory.objects.filter(query & Q(status=0)).count()
        # to avoide Type error ex) 1 - None >> TypeError
        data = {key:( value if value != None else 0) for (key, value) in data.items() }

        query = PurchaseInventory.objects.filter(
            query & Q(status=PurchaseInventory.Status.UNPAID.value)
            ).aggregate(Sum('net_purchases'), Sum('total_amount_paid'))
        query = {key:( value if value != None else 0) for (key, value) in query.items() }

        data["total_amount_unpaid"] = query["net_purchases__sum"] - query["total_amount_paid__sum"]
        return data


    def analysis(self , owner , start_date , end_date):
        # to prevent sql injection as tempview don't allow to pass param
        # the user can't input owner so it's okay if we leave it but this is double check 
        if  not str(owner).isdigit() :
            return None
        with connection.cursor() as cursor:
            cursor.execute("DROP VIEW IF EXISTS myview;")
            # TEMP VIEW doesn't allow as to pass params so be careful when take input from user : sql Injection can occure
            cursor.execute(f"""
            CREATE TEMP VIEW myview AS
            SELECT 
                pu.id ,
                pu.owner_id,
                pu.purchase_date,
                pu.frieght_in ,
				pu.due_date,
				pu.status,
				pu.cost_returned,
				pu.net_purchases,
				pu.num_returend as purchaes_num_returend,
				pu.total_amount_paid as purchaes_total_amount_paid ,
				pu.total_purchases,
                pr.number_of_unit ,
                pr.cost_per_unit ,
                re.num_returned as return_num_returned,
                pa.amount_paid as payment_amount_paid,
                su.first_name || ' ' || su.middle_name || ' ' || su.last_name as supplier_name ,
                inv.item_name  ,
                te.config ,
                te.terms ,
                te.discount_percentage ,
                te.discount_in_days ,
                te.num_of_days_due 	
                
                FROM inventory_purchaseinventory Pu
                LEFT JOIN  inventory_inventoryprice Pr
                ON Pr.purchase_inventory_id = Pu.id
                AND pu.owner_id = {owner} 
                LEFT JOIN inventory_inventoryreturn Re
                ON Re.inventory_price_id = Pr.id
                LEFT JOIN inventory_payinvoice Pa
                ON Pa.purchase_inventory_id = Pu.id
                LEFT JOIN suppliers_supplier Su
                On Pu.supplier_id = Su.id
                LEFT JOIN inventory_inventory inv 
                ON pr.inventory_id = inv.id
                LEFT Join inventory_paymentsalesterm te
                on te.id = pu.term_id
                
                """)

            cursor.execute("""
            SELECT  purchase_date , Sum(net_purchases) , Sum(cost_returned)   FROM myview
            where owner_id = %s AND purchase_date >= %s AND purchase_date <= %s
            GROUP BY purchase_date;
            """ , [owner , start_date , end_date])
            purchases_return_over_time = cursor.fetchall()

            cursor.execute("""
            SELECT item_name, Sum(number_of_unit) , SUM(return_num_returned) From myview
            where owner_id = %s  AND purchase_date >= %s AND purchase_date <= %s
            GROUP By item_name ;
            """ , [owner , start_date , end_date])
            inventory = cursor.fetchall()

            cursor.execute("""
            SELECT supplier_name , sum(total_purchases) as total_purchases , sum(cost_returned)  FROM (
                SELECT supplier_name, total_purchases , cost_returned  FROM myview
                where owner_id = %s  AND purchase_date >= %s AND purchase_date <= %s
                GROUP By id, supplier_name,  total_purchases , cost_returned ) as subquery
            GROUP by supplier_name
            ORDER by total_purchases DESC;
            """ , [owner , start_date , end_date])
            supplier = cursor.fetchall()            
            
          
            cursor.execute("DROP VIEW IF EXISTS myview")
            result = {
                "purchases_return_over_time": purchases_return_over_time ,
                "inventory": inventory ,
                "supplier":supplier,
            }
            
        return result

    def aged_payable(self, owner_id, purchase_date_start, purchase_date_end):
        """
            return aged payable table 
             (aged_payable, Sum(total_amt_unpaid))
        """
        with connection.cursor() as cursor:
            cursor.execute("""
               SELECT aged_payable, Sum(total_amt_unpaid)
                    FROM(
                        SELECT 
                            CASE 
                                WHEN (CURRENT_DATE - due_date) > 90  THEN 'over 90 days'
                                WHEN (CURRENT_DATE - due_date) > 60  THEN '61-90'
                                WHEN (CURRENT_DATE - due_date) > 30  THEN '31-60'
                                WHEN (CURRENT_DATE - due_date) >= 0  THEN '0-30'
                                ELSE 'not over due yet'
                            END as aged_payable,
                            (net_purchases - total_amount_paid) AS total_amt_unpaid
                        FROM inventory_purchaseinventory
                        WHERE status = 0 AND owner_id = %s AND purchase_date >= %s AND purchase_date <= %s
                    ) as aged_payable_table
                GROUP BY aged_payable;
            """, [owner_id, purchase_date_start, purchase_date_end])
            data = cursor.fetchall()
        return data  

    def notDueAndOverDue(self, owner_id, purchase_date_start, purchase_date_end):
        """
            return not due yet:  total amount unpaid
                 Over Dye: total amount unpaid
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    CASE
                        WHEN due_date >=  CURRENT_DATE THEN 'Not Due Yet'
                        WHEN due_date < CURRENT_DATE THEN 'Over Due'
                    END as Due,
                    Sum(net_purchases- total_amount_paid),
                    Count(id)
                FROM inventory_purchaseinventory
                WHERE status = 0 AND owner_id = %s AND purchase_date >= %s AND purchase_date <= %s
                GROUP BY Due;
            """, [owner_id, purchase_date_start, purchase_date_end])
            # data = {key: value for value, key in cursor.fetchall()}  
            data = cursor.fetchall()
        return data  

    def vendors_to_pay (self, owner_id, purchase_date_start, purchase_date_end):
        """
            return amount due for each supplier and aggregate if there is more than one invoice
        """
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    supplier.first_name || ' ' || supplier.middle_name || ' ' || supplier.last_name as full_name,
                    Sum(purchases.net_purchases - purchases.total_amount_paid) as total_amount_due,
                    Count(purchases.id) as open_invoices,
                    Min(purchases.due_date) as min_due_date,
                    Max(purchases.due_date) as max_due_date
                FROM suppliers_supplier as supplier
                JOIN inventory_purchaseinventory as purchases
                ON purchases.supplier_id = supplier.id
                WHERE purchases.status = 0 AND purchases.owner_id = %s AND purchases.purchase_date >= %s AND purchases.purchase_date <= %s
                GROUP BY supplier.id
                ORDER BY total_amount_due  DESC;
            """, [owner_id, purchase_date_start, purchase_date_end])
            # data = {key: value for value, key in cursor.fetchall()}  
            data = cursor.fetchall()
        return data     

        
    def avg_cost_per_unit(self , query):
        """
        avg cost per unit
        """
        data = self.filter(query).aggregate(Avg("inventoryprice__cost_per_unit"))
        return data.get("inventoryprice__cost_per_unit__avg" , 0)

    def std_cost_per_unit(self, query):
        """
        return the stander deviation (change upward ow donward) for cost per unit
        """
        data = self.filter(query).aggregate(StdDev("inventoryprice__cost_per_unit"))
        return data.get("inventoryprice__cost_per_unit__stddev" , 0)

    def max_cost_per_unit(self , query):
        data = self.filter(query).aggregate(Max("inventoryprice__cost_per_unit"))
        return data.get("PurchaseInventory.objects.filter(owner=2" , 0)

    def min_cost_per_unit(self , query):
        data = self.filter(query).aggregate(Min("inventoryprice__cost_per_unit"))
        return data.get("inventoryprice__cost_per_unit__min" , 0)

    def total_units_purchased(self , query):
        """
        sum of of total unit purchased we don't take into account(returned cost this will be different method)
        args: 
            owner
        return 
            the sum of unit's purchases 
        """
        data = self.filter(query).aggregate(Sum("inventoryprice__number_of_unit"))
        return data.get("inventoryprice__number_of_unit__sum" , 0)

    def total_purchases_amount(self , query):
        """
         sum of total purchases amount (freight in or returned purchased not included)
        """
        data = self.prefetch_related("inventoryprice__cost_per_unit","inventoryprice__number_of_unit").filter(query).annotate(
                    total_cost=ExpressionWrapper(
                        F("inventoryprice__cost_per_unit")*F("inventoryprice__number_of_unit"), output_field=FloatField()
                        )).aggregate(Sum("total_cost"))
        return  data["total_cost__sum"] if data["total_cost__sum"] != None else 0

    def total_units_returned(self , query):
        data = self.prefetch_related("inventoryprice__inventoryreturn__num_returned").filter(query).aggregate(Sum("inventoryprice__inventoryreturn__num_returned"))
        return data.get("inventoryprice__inventoryreturn__num_returned__sum" , 0)


    def total_cost_of_units_returned(self , query):
        data = self.select_related("inventoryprice__cost_per_unit","inventoryprice__inventoryreturn__num_returned").filter(query).annotate(
                        total_cost=ExpressionWrapper(
                        F("inventoryprice__cost_per_unit")*F("inventoryprice__inventoryreturn__num_returned"), output_field=FloatField()
                        )).aggregate(Sum("total_cost"))
        return data["total_cost__sum"] if data["total_cost__sum"] != None else 0

    def net_purchases(self , query):
        return PurchaseManager.total_purchases_amount(self , query) - PurchaseManager.total_cost_of_units_returned(self ,query)

    def total_amount_paid(self , query):
        # this one for PAID invoice already on Cash
        # i have discoverd this is not effiecient way  i should use raw sql instead
        # PAID = [obj.net_purchase for obj in self.filter(owner=owner) if obj.status == "PAID"]
        # this query of unpaid invoice anfd then we pay it partuaily or full the amount
        # query = self.filter(owner=owner).aggregate(Sum("payinvoice__amount_paid"))
        data = self.filter(query).aggregate(Sum("total_amount_paid"))
        return data["total_amount_paid__sum"] if data["total_amount_paid__sum"] != None else 0

    def total_amount_unpaid(self, query):
        return PurchaseManager.net_purchases(self ,query) - PurchaseManager.total_amount_paid(self ,query)

    def unique_supplier(self, query):
        return set([obj.supplier for obj in self.filter(query)])

    def group_by_supplier(self , query):
        pass
        # data = {
        #     "Supplier": [] , 
        #     "net_pruchases": [] ,
        #     "total_amount_unpaid": [] ,
        #     "total_amount_paid" : [] , 
        #     "total_cost_of_units_returned": [] ,
        #     "total_units_returned": [] ,
        #     "total_purchases_amount" : [] ,
        #     "total_units_purchased": []

        # }

        # for supplier in self.unique_supplier(query):
        #     data["Supplier"].append(supplier.full_name)
        #     query = PurchaseInventory.objects.filter(query , supplier = supplier)
        #     data["net_pruchases"].append(PurchaseManager.net_purchases(query , owner))
        #     data["total_purchases_amount"].append(PurchaseManager.total_purchases_amount(query ,  owner))
        #     data["total_amount_unpaid"].append(PurchaseManager.total_amount_unpaid(query , owner))
        #     data["total_amount_paid"].append(PurchaseManager.total_amount_paid(query , owner))
        #     data["total_cost_of_units_returned"].append(PurchaseManager.total_cost_of_units_returned(query , owner))
        #     data["total_units_purchased"].append(PurchaseManager.total_units_purchased(query , owner))
        #     data["total_units_returned"].append(PurchaseManager.total_units_returned(query , owner))

        # return data


    def join_data(self , owner , start_date , end_date):
        """
        Join all table related to purchases 
            -
            
        """
       
        with connection.cursor() as cursor:
            query = cursor.execute("""
               SELECT 
                pu.id ,
                pu.owner_id ,
                pu.purchase_date,
                pu.frieght_in ,
                pr.number_of_unit ,
                pr.cost_per_unit ,
                Re.date , 
                re.num_returned,
                pa.amount_paid ,
                su.first_name ,
                su.middle_name ,
                su.last_name ,
                inv.item_name ,
                acc.account , 
                te.config ,
                te.terms ,
                te.discount_percentage ,
                te.discount_in_days ,
                te.num_of_days_due 	
                
                FROM inventory_purchaseinventory Pu
                LEFT JOIN  inventory_inventoryprice Pr
                ON Pr.purchase_inventory_id = Pu.id
                AND pu.owner_id = %s AND pu.purchase_date >= %s AND pu.purchase_date <= %s

                LEFT JOIN inventory_inventoryreturn Re
                ON Re.inventory_price_id = Pr.id
                LEFT JOIN inventory_payinvoice Pa
                ON Pa.purchase_inventory_id = Pu.id
                JOIN suppliers_supplier Su
                On Pu.supplier_id = Su.id
                JOIN inventory_inventory inv 
                ON pr.inventory_id = inv.id
                Join inventory_paymentsalesterm te
                on te.id = pu.term_id
                JOIN sole_proprietorship_accounts  acc 
                ON acc.id = te.general_ledeger_account_id

                """, [owner , start_date , end_date])
            result = query.fetchall()
        return result


class PurchaseInventory(DueDateMixin, models.Model):
    """
    Note freight in cost which inccure when you purchase your inventory will charge only on the first
    form inventory in formset
    """
    class Meta:
        indexes = [
            models.Index(fields=['status'], name='pur_status_idx'),
            models.Index(fields=['purchase_date'], name='purchase_date_idx'),

        ]

    class Status(models.IntegerChoices):
        UNPAID = 0 , _("UNPAID")
        PAID = 1 , _("PAID")

    status = models.IntegerField(choices=Status.choices)
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    purchase_date = models.DateField()
    due_date = models.DateField(
        help_text="optional if you want to specify it by yourself",
        null = True ,
        blank = True,
    )

    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    term = models.ForeignKey(PaymentSalesTerm, on_delete=models.CASCADE)
    frieght_in = models.FloatField(default=0)
    num_returend = models.IntegerField(blank=True, null=True, default=0)
    cost_returned =  models.FloatField(blank=True, null=True, default=0)
    total_purchases = models.FloatField(blank=True, null=True)
    net_purchases = models.FloatField(blank=True, null=True)
    total_amount_paid = models.FloatField(blank=True, null=True, default=0)
    allowance = models.FloatField(blank=True, null=True, default=0)
    objects = models.Manager() # the default_managers
    purchases = PurchaseManager()


    def check_status(self):
        """
        Check if this invoice PAID or UNPAID
        """
        if self.term.terms == PaymentSalesTerm.Term.CASH.value:
            return "PAID"
        elif self.check_net_purchase() == self.check_total_amount_paid():
            return "PAID"
        elif self.check_net_purchase() * ((100- self.term.discount_percentage) / 100) == self.check_total_amount_paid() and self.payinvoice_set.count() ==1 and self.payinvoice_set.first().date <=  (self.purchase_date.date() + timedelta(self.term.discount_in_days) ) : 
            return "PAID"
        else:
            return "UNPAID"

    # def check_status(self):
    #     """
    #     Check if this invoice PAID or UNPAID
    #     """
    #     net_purchases = self.check_net_purchase() 
    #     total_amount_paid = self.check_total_amount_paid()
    #     # if there is dicount
    #     try:
    #         last_paid_date = self.payinvoice_set.order_by('-date').first().date
    #     except AttributeError:
    #         last_paid_date = None
    
    #     is_there_is_dicount, amount_if_there_is_dicount=  None, None
    #     try:
    #         amount_if_there_is_dicount =    self.net_purchases * ( (100 - self.term.discount_percentage) /100) 
    #     except TypeError:
    #         pass

    #     if (last_paid_date != None and  self.due_date != None and last_paid_date <= self.due_date and
    #          self.term.discount_percentage > 0 and
    #            total_amount_paid == amount_if_there_is_dicount):
    #         is_there_is_dicount = True
        
    #     if is_there_is_dicount and amount_if_there_is_dicount == total_amount_paid:
    #         return "PAID"

    #     if self.term.terms == PaymentSalesTerm.Term.CASH.value or (net_purchases ==  total_amount_paid and (total_amount_paid!= 0 and net_purchases != 0 )) or self.status == 1:
    #         return "PAID"
    #     else:
    #         return  "UNPAID"

    



    def check_allowance(self) -> float:
        query = self.inventoryallowance_set.aggregate(Sum('amount'))
        return query['amount__sum'] if query['amount__sum']  != None else 0

    
    def check_num_cost_of_returned_inventory(self) -> tuple:
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

    def check_total_amount(self) -> float:
        """amount of purchase whether on account or paid cash"""
        # reurn dict for total amount of purchases
        query = self.inventoryprice_set.annotate(
                    total_cost=ExpressionWrapper(
                        F("cost_per_unit")*F("number_of_unit"), output_field=FloatField()
                        )).aggregate(total_amount=Sum("total_cost"))

        print('total_amount',query["total_amount"])
        return query["total_amount"] if query["total_amount"] != None else 0

    
    def check_net_purchase(self):
        """
        return amount of purchase take into our account if we return some inventory
        
        """
        return self.check_total_amount() - self.check_num_cost_of_returned_inventory()[1] - self.check_allowance()

    
    def check_total_amount_paid(self):
        """
        return  total amount paid for specific invoice
        """
        query = self.payinvoice_set.aggregate(Sum("amount_paid"))["amount_paid__sum"]
        if query == None:
            if self.term.terms == PaymentSalesTerm.Term.CASH.value:
                return self.check_net_purchase()
            else:
                return 0
        return query


    def check_total_amount_unpaid(self):
        return self.check_net_purchase() - self.check_total_amount_paid()

    def save(self, *args, **kwargs):
        self.due_date = self.check_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"invoice number:{self.pk}"
    
    # we will add in the future the address for the supplier and the ship address

class PayInvoice(models.Model):
    purchase_inventory = models.ForeignKey(PurchaseInventory , on_delete=models.CASCADE)
    date = models.DateField()
    amount_paid = models.FloatField()


    def first_patment(self):
        """
        return True if this your first payment
        """
        return self.purchase_inventory.payinvoice_set.count() == 0

    def check_amount_you_will_pay(self):
        amount_you_will_pay, discount = None, None
        amount_paid = self.purchase_inventory.total_amount_paid
        if self.purchase_inventory.status == PurchaseInventory.Status.PAID.value:
            amount_you_will_pay = 0
        else:
            if self.first_patment() and self.purchase_inventory.term.discount_percentage > 0 and self.date <= (self.purchase_inventory.purchase_date.date() + timedelta(self.purchase_inventory.term.discount_in_days)):
                amount_you_will_pay = self.purchase_inventory.net_purchases * ( (100 - self.purchase_inventory.term.discount_percentage) /100) - amount_paid
                discount = True
            else:
                amount_you_will_pay = self.purchase_inventory.net_purchases - amount_paid
                discount = False
        return  amount_you_will_pay, discount


    def clean(self):
        amount_you_will_pay, discount = self.check_amount_you_will_pay()
        warning_message = f"""
        Paid amount can't be greater than invoice cost {amount_you_will_pay} {'after applying dicount' if discount else '' }
        """
        if self.amount_paid > amount_you_will_pay:
            raise ValidationError({
        "amount_paid":ValidationError(_(warning_message) , code="invaild") , 
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


    @cached_property
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

    def vaildate_return(self):
        """
        # num of returned unit can't be greater than num units purchased
        """
        message, status = None, None
        if self.inventory_price.inventoryreturn_set.exists():
            agg_data =self.inventory_price.inventoryreturn_set.aggregate(total_num_returned=Sum("num_returned"))
            avilable = self.inventory_price.number_of_unit - agg_data.get("total_num_returned", 0)
            if self.num_returned > avilable:
                message = f"num of returned unit {self.num_returned} can't be greater than num units purchase take into our account previous returned: {avilable}"
                status = False

        else:
            if self.num_returned > self.inventory_price.number_of_unit:
                message = f"num of returned unit {self.num_returned} can't be greater than num units purchase {self.inventory_price.number_of_unit}"
                status = False
        return status, message

    def clean(self):
        STATUS, MESSAGE = self.vaildate_return()
        if STATUS == False:
            raise ValidationError({
        "num_returned":ValidationError(_(MESSAGE) , code="invaild") , 
        })


    def __str__(self):
        return f"return {self.num_returned} of {self.inventory_price.inventory.item_name}"


class InventoryAllowance(models.Model):
    """
     Allowance Model it's like Purchase Return Except the inventory keep with you
    """
    purchase_inventory =   models.ForeignKey(PurchaseInventory, on_delete=models.CASCADE)
    inventory_price = models.ForeignKey(InventoryPrice, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.FloatField(blank=True, null=True)

    def clean(self):
        invoice_cost = self.purchase_inventory.check_net_purchase()
        warning_message = f"""
        Allowance amount can't be greater than invoice cost {invoice_cost}
        """
        if self.amount > invoice_cost:
            raise ValidationError({
        "amount":ValidationError(_(warning_message) , code="invaild") , 
        })
       

    def __str__(self):
        return f"{self.date}: {self.purchase_inventory} Return ${self.amount}"



def current_date():
    return timezone.now().date()

class Sale(DueDateMixin, models.Model):
    customer = models.ForeignKey('Customers_Sales.Customer', on_delete=models.CASCADE)
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    term = models.ForeignKey(PaymentSalesTerm, on_delete=models.CASCADE)

    frieght_out = models.FloatField(default=0)
    sales_date = models.DateField(default=current_date)
    due_date = models.DateField(
        help_text="optional if you want to specify it by yourself",
        null = True ,
        blank = True,
    )
    objects = models.Manager() # the default_managers
    sales = SaleManager()




    @cached_property
    def total_amount_paid(self):
        query = self.salespayment_set.aggregate(Sum('amount'))
        if query['amount__sum'] != None:
            return query['amount__sum']
        else:
            if self.term.terms == PaymentSalesTerm.Term.CASH.value:
                return self.net_sales
            else:
                return 0

    @cached_property
    def first_payment(self) -> bool:
        """
        return True if this first payment
        """
        return True if self.salespayment_set.count() == 0 else False


    @cached_property
    def amount_if_there_discount(self):
        return self.net_sales * ((100- self.term.discount_percentage) / 100)

    @cached_property
    def paid(self) -> bool:
        if self.term.terms == PaymentSalesTerm.Term.CASH.value:
            return True
        elif self.net_sales == self.total_amount_paid:
            return True
        elif self.net_sales * ((100- self.term.discount_percentage) / 100) == self.total_amount_paid and self.salespayment_set.count() ==1 and self.salespayment_set.first().date <=  (self.sales_date + timedelta(self.term.discount_in_days) ) : 
            return True
        else:
            return False




    def ARorCash(self):
        """
        check if you sell service or invenotry bu cash or on account
        """
        if self.term.terms  ==  PaymentSalesTerm.Term.CASH.value:
            return self.term.cash_account
        return self.term.accounts_receivable


    @cached_property
    def sales_allowance(self):
        query = self.salesallowance_set.aggregate(Sum('amount'))
        return query['amount__sum'] if query['amount__sum'] != None else 0


    @cached_property
    def num_units_returned(self):
        query = self.salesreturn_set.aggregate(Sum('num_returned'))
        return query['num_returned__sum'] if query['num_returned__sum'] != None else 0


    @cached_property
    def sales_return(self):
        query = self.salesreturn_set.annotate(
            total=ExpressionWrapper(F('num_returned') * F('sold_item__sale_price'), output_field=FloatField())
        ).aggregate(
            Sum('total')
        )
        return query['total__sum'] if query['total__sum'] != None else 0


    @cached_property
    def sub_total(self):
        """
        return sub total for the sales without considering sales return and allowance
        """
        query = self.sold_item_set.values('sale_price', 'quantity').annotate(
            total= F('sale_price') * F('quantity')
            ).aggregate(
                Sum('total')
            )
        return query['total__sum'] if query['total__sum'] != None else 0

    @cached_property
    def net_sales(self):
        """
            net sales Ignoring discount
        """
        return self.sub_total - self.sales_return - self.sales_allowance

    @cached_property
    def total_amount_unpaid(self):
        return self.net_sales - self.total_amount_paid

    def save(self, *args, **kwargs):
        self.due_date = self.check_due_date()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Sales id: {self.pk}'


class Sold_Item(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryPrice, on_delete=models.CASCADE)
    sale_price = models.FloatField(null=False, blank=False)
    quantity = models.FloatField(null=False, blank=False)


    def units_sold(self):
        query = self.item.sold_item_set.aggregate(Sum('quantity'))
        return query['quantity__sum'] if query['quantity__sum'] != None else 0

    def num_of_purchase_return(self):
        purchase_return_q = self.item.inventoryreturn_set.aggregate(Sum('num_returned'))
        return purchase_return_q['num_returned__sum'] if purchase_return_q['num_returned__sum'] != None else 0


    def units_from_sales_return(self):
        query = self.salesreturn_set.aggregate(Sum('num_returned'))
        return query['num_returned__sum'] if query['num_returned__sum'] !=None else 0

    def units_available_for_sales(self):
        return self.item.number_of_unit - self.num_of_purchase_return() - self.units_sold() + self.units_from_sales_return()


   

    def quantity_g_units_available_for_sales(self) -> tuple:
        """
         return True if the number of item sold greater than  units availble for sales
        """
        units_available_for_sales = self.units_available_for_sales()
        Message = f'The Quantity {self.quantity} cannot be greater than units available for sales {units_available_for_sales}'
        return self.quantity > units_available_for_sales , Message


    def clean(self):
        super().clean()
        invaild, MESSAGE =  self.quantity_g_units_available_for_sales()
        if invaild:
            raise ValidationError({
                    "quantity":ValidationError(_(MESSAGE) , code="invaild") , 
                    })

    

    def __str__(self):
        return f'{self.item}'


class SalesReturn(models.Model):
    """
        Sales Return Model
    """
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    sold_item = models.ForeignKey(Sold_Item, on_delete=models.CASCADE)
    date = models.DateField()
    num_returned = models.PositiveIntegerField()

    def vaildate_num_returned(self):
        available_for_return = self.sold_item.units_sold() - self.sold_item.units_from_sales_return()
        Message = f'The Quantity {self.num_returned} return cannot be greater than units available_for_return {available_for_return}'
        return self.num_returned > available_for_return , Message


    def clean(self):
        invaild, MESSAGE =  self.vaildate_num_returned()
        if invaild:
            raise ValidationError({
                    "num_returned":ValidationError(_(MESSAGE) , code="invaild") , 
                    })

    


    def __str__(self):
        return f'return {self.num_returned} unit for {self.sold_item} on {self.date}'



class SalesAllowance(models.Model):
    sales = models.ForeignKey(Sale, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.FloatField()

    def __str__(self):
        return f'Allowance {self.date}: {self.amount}'


class SalesPayment(models.Model):
    sales = models.ForeignKey(Sale, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.FloatField()


    @cached_property
    def first_payment(self) -> bool:
        """
        return True if this first payment
        """
        return True if self.sales.salespayment_set.count() == 0 else False

    def discount(self) -> bool:
        """
        return True if the due of payment <= due date and there is a discount otherwise False
        """
        if self.sales.due_date:
            if self.sales.term.discount_percentage > 0  and self.date <= (self.sales.sales_date + timedelta(self.sales.term.discount_in_days) ):
                return True
        return False


    def amount_you_will_pay(self):
        """
            return the amounth that you should pay
        """
        if self.first_payment and self.discount():
            return self.sales.amount_if_there_discount
        return self.sales.net_sales - self.sales.total_amount_paid


    def validate_amount(self):
        invaild, MESSAGE = None, None
        if self.amount > self.amount_you_will_pay():
            MESSAGE = f"the amount {self.amount} you will pay can't be greater than {self.amount_you_will_pay()}"
            invaild = True
        return invaild, MESSAGE

    def clean(self):
        invaild, MESSAGE =  self.validate_amount()
        if invaild:
            raise ValidationError({
                    "amount":ValidationError(_(MESSAGE) , code="invaild") , 
                    })

    


    def __str__(self):
        return f'payment {self.amount} for {self.sales} on date {self.date}'