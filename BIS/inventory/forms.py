from django import forms
from inventory.models import (PurchaseInventory , PaymentSalesTerm , InventoryPrice ,
    Inventory, InventoryReturn , PayInvoice, InventoryImag, InventoryAllowance, Sale, Sold_Item,
    SalesReturn, SalesAllowance, SalesPayment
    )
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout , Row , Column  , Div  
from crispy_forms.bootstrap import InlineRadios
from suppliers.models import Supplier
from django.forms import formset_factory, modelformset_factory
from django.utils import timezone
from sole_proprietorship.models import Accounts
import django_filters
from django.utils import timezone
from django.forms import inlineformset_factory
from django.db.models.expressions import RawSQL
from Customers_Sales.models import Customer
from home.utils import DateField, DateMixin
from django.shortcuts import get_object_or_404 

ImageFormSet = inlineformset_factory(
    Inventory, InventoryImag, fields=('img',), extra = 3
    )



class PurchaseFilter(django_filters.FilterSet, DateMixin):
    class Meta:
        model = PurchaseInventory
        fields = {
                'status': ['exact'],
                'purchase_date': ['gte', 'lte'],
                'due_date': ['gte', 'lte'],
                'term': ['exact'],
                'supplier': ['exact'],
                'num_returend': ['gte', 'lte'],  
                'cost_returned': ['gte', 'lte'],  
                'total_purchases': ['gte', 'lte'],  
                'net_purchases': ['gte', 'lte'],  
                'total_amount_paid': ['gte', 'lte'],  
                }

    def __init__(self,   **kwargs):
        super().__init__(**kwargs)
        self.date(
            [
                DateField(field='purchase_date__gte', initial=False),
                DateField(field='purchase_date__lte', initial=False),
                DateField(field='due_date__gte', initial=False),
                DateField(field='due_date__lte', initial=False),

            ],
            django_filter=True
        )
       


class PaymentSalesTermForm(forms.ModelForm):
    class Meta:
        model = PaymentSalesTerm
        fields = ['config' , 'terms' , 'num_of_days_due' , 'discount_in_days' , 'discount_percentage' , 'sales_revenue',
                 "accounts_payable",'pay_freight_out', 'freight_in_account', 'cash_account','freight_out_account', 'COGS',
                 'accounts_receivable', 'sales_return', 'sales_allowance', 'sales_discount'
                 ]

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super().__init__(*args, **kwargs)
        queryset = Accounts.objects.filter(owner=self.owner)
        for account in ['sales_discount', 'sales_return', 'sales_allowance','sales_revenue','accounts_receivable', 'cash_account', 'accounts_payable', 'freight_in_account', 'freight_out_account', 'COGS']:
            self.fields[account].queryset = queryset
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'config',
            Row( 
                Column(InlineRadios('terms') , css_class="col-4"),
                Column('num_of_days_due' , 'discount_in_days' , 'discount_percentage')
            ),
            Row(
                Column('freight_in_account', 'freight_out_account', 'sales_revenue'), 
                Column('COGS', 'cash_account', 'accounts_payable'),
                Column('accounts_receivable', 'sales_return', 'sales_allowance', 'sales_discount')
            ),
            Row(
                'pay_freight_out'
            )
            
        )
        
        self.helper.form_tag = False


class PurchaseInventoryForm(forms.ModelForm, DateMixin):
    class Meta:
        model = PurchaseInventory
        fields = ['supplier' , 'purchase_date' ,'term', 'due_date' , 'frieght_in']


    def __init__(self,owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(owner=owner)
        self.fields["term"].queryset = PaymentSalesTerm.objects.filter(owner=owner)
        self.date(
                [
                    DateField(field='purchase_date', initial=True),
                    DateField(field='due_date', initial=False)

                ]
        )

        self.helper = FormHelper()
        self.helper.layout = Layout( 
            Row( 
                Column('supplier'),
                Column('purchase_date' , 'term' ,'due_date' , 'frieght_in') )
        )
        self.helper.form_tag = False


class SalesForm(forms.ModelForm):
    class Meta:
        model = Sale
        exclude = ('owner', 'sub_total')
        widgets = {
            'sales_date': forms.widgets.DateInput(attrs={'type': 'date'}),
            'due_date': forms.widgets.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self,owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.filter(owner=owner)
        self.fields["term"].queryset = PaymentSalesTerm.objects.filter(owner=owner)

        self.helper = FormHelper()
        self.helper.layout = Layout( 
            Row( 
                Column('customer'),
                Column('sales_date' , 'term' ,'due_date' , 'frieght_out') )
        )
        self.helper.form_tag = False
    
class InventoryPriceForm(forms.ModelForm):
    class Meta:
        model = InventoryPrice
        fields = ['inventory' , 'cost_per_unit' , 'number_of_unit']

    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner = owner
        self.fields["inventory"].queryset = Inventory.objects.filter(owner=owner)




class SoldItemForm(forms.ModelForm):
    class Meta:
        model = Sold_Item
        exclude = ('sale',)
    
    def __init__(self, owner_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('owner_id', owner_id)
        SQL_LITE = """
            SELECT  p.id
            FROM inventory_inventoryprice as p
            LEFT JOIN inventory_purchaseinventory 
            ON inventory_purchaseinventory.id = p.purchase_inventory_id
            LEFT JOIN inventory_inventoryreturn as r
            ON p.id = r.inventory_price_id
            LEFT JOIN inventory_sold_item as s
            ON s.item_id = p.id
            WHERE inventory_purchaseinventory.owner_id = %s
            GROUP BY p.id
            HAVING (number_of_unit - ifnull(Sum(r.num_returned) ,0) - ifnull(Sum(s.quantity), 0) )  > 0
         """

        self.fields['item'].queryset = InventoryPrice.objects.select_related('inventory').filter(id__in =RawSQL(SQL_LITE, [owner_id])).all()

class InventoryPriceFormsetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout( 
            Div(Row(Column('inventory') , Column('cost_per_unit') , Column('number_of_unit') ) , css_class="link-formset" )
        )
        self.form_tag = False


class ImageFormsetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout( 
            Div(Row(Column('img') ,  css_class="link-formset" ))
        )
        self.form_tag = False


class ImageForm(forms.ModelForm):
    class Meta:
        model = InventoryImag
        exclude = ('inventory', )


InventoryPriceFormset = formset_factory(InventoryPriceForm)
SoldItemFormset =  formset_factory(SoldItemForm)
ImageFormest = formset_factory(ImageForm)

class InventoryReturnForm(forms.ModelForm):
    class Meta:
        model = InventoryReturn
        fields = '__all__'
        widgets = {
            'date': forms.widgets.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        self.fields["date"].initial = timezone.localdate()
        
class DateInput(forms.DateInput):
    input_type = 'date'

class PayInvoiceForm(forms.ModelForm):
    class Meta:
        model = PayInvoice
        fields = '__all__'

    def __init__(self , *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super().__init__(*args, **kwargs)
        self.fields["purchase_inventory"].queryset = PurchaseInventory.objects.filter(owner=self.owner , status=0)
        self.fields['date'].widget = DateInput()
        self.fields['date'].initial = timezone.now()




class ReportingPeriodConfigForm(forms.Form):
    start_date = forms.DateField(widget = DateInput)
    end_date = forms.DateField(widget = DateInput)
  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'start_date', 'end_date'  
        )
        self.helper.form_tag = False
        self.helper.disable_csrf = True


        
class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        exclude = ('owner',)


class InventoryAllowanceForm(forms.ModelForm, DateMixin):
    class Meta:
        model = InventoryAllowance
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date(
                [
                    DateField(field='date', initial=True)
                ]
            )


class SalesReturnForm(forms.ModelForm, DateMixin):
    class Meta:
        model = SalesReturn
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.sales_pk = kwargs.pop('sales_pk', None)
        self.sales_item_pk = kwargs.pop('sales_item_pk', None)
        self.owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        self.date(
                [
                    DateField(field='date', initial=True)
                ]
        )
        self.fields['sale'].queryset = Sale.objects.filter(owner=self.owner)
        self.fields['sold_item'].queryset= Sold_Item.objects.filter(sale__owner=self.owner).select_related('item')
        
        if self.sales_pk != None and self.sales_item_pk != None:
            self.fields['sale'].initial = get_object_or_404(Sale, pk=self.sales_pk, owner=self.owner)
            self.fields['sold_item'].initial = get_object_or_404(Sold_Item, pk=self.sales_item_pk, sale__owner=self.owner)
            self.fields['sale'].widget.attrs['readonly'] = True
            self.fields['sold_item'].widget.attrs['readonly'] = True




class SalesInitMixin:
  def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner', None)
        self.sales_pk = kwargs.pop('sales_pk', None)
        super().__init__(*args, **kwargs)
        self.date(
                [
                    DateField(field='date', initial=True)
                ]
        )
        self.fields['sales'].queryset = Sale.objects.filter(owner=self.owner)
        if self.sales_pk:
            self.fields['sales'].initial = get_object_or_404(Sale, pk=self.sales_pk, owner=self.owner)



class SalesAllowaceForm(SalesInitMixin, forms.ModelForm, DateMixin):
    class Meta:
        model = SalesAllowance
        fields = '__all__'

  
class SalesPaymentForm(SalesInitMixin, forms.ModelForm, DateMixin):
    class Meta:
        model = SalesPayment
        fields = '__all__'

   