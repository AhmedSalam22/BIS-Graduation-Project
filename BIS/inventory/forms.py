from django import forms
from inventory.models import PurchaseInventory , PaymentSalesTerm , InventoryPrice , Inventory, InventoryReturn , PayInvoice
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout , Row , Column  , Div  
from crispy_forms.bootstrap import InlineRadios
from suppliers.models import Supplier
from django.forms import formset_factory
from django.utils import timezone
from sole_proprietorship.models import Accounts

class PaymentSalesTermForm(forms.ModelForm):
    class Meta:
        model = PaymentSalesTerm
        fields = ['config' , 'terms' , 'num_of_days_due' , 'discount_in_days' , 'discount_percentage' , "general_ledeger_account", 'freight_in_account']

    def __init__(self, *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super().__init__(*args, **kwargs)
        self.fields['general_ledeger_account'].queryset = Accounts.objects.filter(owner=self.owner)
        self.fields['freight_in_account'].queryset = Accounts.objects.filter(owner=self.owner)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'config', 
            'general_ledeger_account',
            Row( 
                Column(InlineRadios('terms') , css_class="col-4"),
                Column('num_of_days_due' , 'discount_in_days' , 'discount_percentage') ),
            'freight_in_account'
            
        )
        
        self.helper.form_tag = False


class PurchaseInventoryForm(forms.ModelForm):
    class Meta:
        model = PurchaseInventory
        fields = ['supplier' , 'num' , 'purchase_date' ,'term', 'due_date' , 'frieght_in']
        widgets = {
            'purchase_date': forms.widgets.DateInput(attrs={'type': 'date'}),
            'due_date': forms.widgets.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self,owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["supplier"].queryset = Supplier.objects.filter(owner=owner)
        self.fields["term"].queryset = PaymentSalesTerm.objects.filter(owner=owner)

        self.helper = FormHelper()
        self.helper.layout = Layout( 
            Row( 
                Column('supplier'),
                Column('num' , 'purchase_date' , 'term' ,'due_date' , 'frieght_in') )
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

class InventoryPriceFormsetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout( 
            Div(Row( 'inventory' , 'cost_per_unit' , 'number_of_unit' ) , css_class="link-formset" )
        )
        self.form_tag = False


InventoryPriceFormset = formset_factory(InventoryPriceForm)

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
        

class PayInvoiceForm(forms.ModelForm):
    class Meta:
        model = PayInvoice
        fields = '__all__'

    def __init__(self , *args, **kwargs):
        self.owner = kwargs.pop('owner')
        super().__init__(*args, **kwargs)
        self.fields["purchase_inventory"].queryset = PurchaseInventory.objects.filter(owner=self.owner , status=0)



class DateInput(forms.DateInput):
    input_type = 'date'

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


        

