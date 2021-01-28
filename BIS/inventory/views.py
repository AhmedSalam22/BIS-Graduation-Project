from django.shortcuts import render , redirect , get_object_or_404 
from django.urls import reverse_lazy
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView , OwnerDetailView
from inventory.models import PaymentSalesTerm , Inventory , InventoryReturn , InventoryPrice , PurchaseInventory
from django.views.generic import View , TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.forms import ( PaymentSalesTermForm , PurchaseInventoryForm , InventoryPriceFormset ,
                                 InventoryPriceFormsetHelper , InventoryReturnForm , PayInvoiceForm  , ReportingPeriodConfigForm )
from sole_proprietorship.models import Journal
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum , Q
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO

def get_graph():
    """
    reference :https://www.youtube.com/watch?v=jrT6NiM46jk
    """
    buffer = BytesIO()
    plt.savefig(buffer , format="png")
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph

# Create your views here.
class CreateTermView(OwnerCreateView):
    form_class  = PaymentSalesTermForm
    template_name = "inventory/term_form.html"

class UpdateTermView(OwnerUpdateView):
    model = PaymentSalesTerm
    form_class  = PaymentSalesTermForm
    template_name = "inventory/term_form.html"


class ListTermView(OwnerListView):
    model = PaymentSalesTerm
    template_name = "inventory/term_list.html"
    paginate_by = 5
    ordering = ["config"]

class DeleteTermView(OwnerDeleteView):
    model = PaymentSalesTerm
    template_name = "inventory/term_delete.html"


class CreatePurchaseInventoryView(LoginRequiredMixin, View):
    template_name = "inventory/purchase_form.html"
    success_url = None
    inventory_price_formset_helper = InventoryPriceFormsetHelper()

    def save_journal_transaction(self , owner , purchase_inventory_form , inventory_price_form):
        """"
        Purchase Inventory transaction:
        transaction1:Inventory Debit by                      xxxx
        transaction2:     Cash or Accounts payable Credit by       xxx
        """
        
        transaction1 = Journal(owner=owner,
                account = inventory_price_form.inventory.general_ledeger_account,
                date = purchase_inventory_form.purchase_date ,
                balance= inventory_price_form.number_of_unit *  inventory_price_form.cost_per_unit ,
                transaction_type="Debit" , 
                comment=f"purchase inventory {inventory_price_form.inventory}, number of units purchased{inventory_price_form.number_of_unit}")
        transaction1.save()
        transaction2 = Journal(owner=owner,
                    account = purchase_inventory_form.term.general_ledeger_account,
                    date = purchase_inventory_form.purchase_date ,
                    balance= inventory_price_form.number_of_unit *  inventory_price_form.cost_per_unit ,
                    transaction_type="Credit" , 
                    comment=f"purchase {inventory_price_form.inventory}")
        transaction2.save()

    def freight_in_cost(self,owner, purchase_inventory_form , inventory_price_form):
        """
        for now if there is freight in cost we will use the account in the term wheter
        it's CASH or Accounts Payable
        """
        transaction1 = Journal(owner=owner,
                account = inventory_price_form.inventory.general_ledeger_account,
                date = purchase_inventory_form.purchase_date ,
                balance= purchase_inventory_form.frieght_in ,
                transaction_type="Debit" , 
                comment=f"freight in cost {inventory_price_form.inventory}")
        transaction1.save()
        transaction2 = Journal(owner=owner,
                    account = purchase_inventory_form.term.general_ledeger_account,
                    date = purchase_inventory_form.purchase_date ,
                    balance=  purchase_inventory_form.frieght_in ,
                    transaction_type="Credit" , 
                    comment=f"freight in cost {inventory_price_form.inventory}")
        transaction2.save()

        
    def get(self , request , *args, **kwargs):
        owner = self.request.user
        purchase_inventory_form = PurchaseInventoryForm(owner)
        inventory_price_formset = InventoryPriceFormset(form_kwargs={'owner': owner})

        ctx = {
            "purchase_inventory_form":purchase_inventory_form,
            "inventory_price_formset":inventory_price_formset,
            "inventory_price_formset_helper": self.inventory_price_formset_helper,
        }
        return render(request , self.template_name , ctx )

    def post(self , request , *args , **kwargs):
        """
            save the form data if is vaild
            fright-in charge will charge of first inventory form in formset
        """
        owner = self.request.user
        purchase_inventory_form = PurchaseInventoryForm(data=request.POST , owner=owner)
        inventory_price_formset = InventoryPriceFormset(request.POST , form_kwargs={'owner': owner})
        if purchase_inventory_form.is_valid() and inventory_price_formset.is_valid():
            form1 = purchase_inventory_form.save(commit=False)
            form1.owner = owner
            form1.status = 0 if form1.check_status() =="UNPAID" else 1 
            form1.save()
            # print("form1")
            # print(dir(form1))
            counter = 1
            for form in inventory_price_formset:
                form2 = form.save(commit=False)
                form2.purchase_inventory = form1
                form2.save()
                # print(dir(form2))
                # print(form2.inventory.general_ledeger_account)
                # print(form1.purchase_date)
                # print(form2.number_of_unit)
                # print(form2.cost_per_unit)
                self.save_journal_transaction(owner=owner,
                    purchase_inventory_form=form1,
                    inventory_price_form = form2
                    )
                # fright in charge only in first invenory form in formset
                if counter == 1 and  form1.frieght_in > 0:
                    self.freight_in_cost(owner = owner, 
                        purchase_inventory_form = form1,
                        inventory_price_form = form2)
                counter +=1
            form1.update_and_save()
            # form1.total_purchases =  form1.check_total_amount()
            # form1.net_purchases = form1.check_net_purchase()
            # form1.total_amount_paid = form1.check_total_amount_paid()
            # form1.status = 0 if form1.check_status() =="UNPAID" else 1
            # form1.due_date = form1.check_due_date()
            # form1.save()

            return redirect(self.success_url)
        ctx = {
                    "purchase_inventory_form":purchase_inventory_form,
                    "inventory_price_formset":inventory_price_formset,
                    "inventory_price_formset_helper": self.inventory_price_formset_helper,
                }
        return render(request , self.template_name , ctx )

class ListInventoryView(OwnerListView):
    model = Inventory
    template_name = "inventory/inventory_list.html"
    paginate_by = 20

    def get_queryset(self):
        qs = super().get_queryset()
        # selected related used to cash the result from FK without hit the database
        return qs.select_related().all()

    
class DetailInventoryView(OwnerDetailView):
    model = Inventory
    template_name = "inventory/inventory_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["last_unit"] =  context["inventory"].inventoryprice_set.order_by("-purchase_inventory__purchase_date").first()
        # prices >> all the hisorcal data for purchases
        context["prices"] = context["inventory"].inventoryprice_set.order_by("-purchase_inventory__purchase_date").select_related()
        return context
    

class HomeView(TemplateView):
    template_name = "inventory/index.html"


class CreatePurchaseReturnView(LoginRequiredMixin ,View):
    template_name = "inventory/purchase_return_form.html"
    success_url = "inventory:detail_inventory"

    def save_journal_transaction(self , owner , inventory_return):
        """
         A/P or CASH Debit by xxx
            Inventory Credit by     xxx
        """
        date = inventory_return.date
        balance = inventory_return.num_returned * inventory_return.inventory_price.cost_per_unit
        transaction1 = Journal(owner=owner,
                account = inventory_return.inventory_price.inventory.general_ledeger_account,
                date = date ,
                balance= balance,
                transaction_type="Credit" , 
                comment=f"return inventory")
        transaction1.save()
        transaction2 = Journal(owner=owner,
                    account = inventory_return.inventory_price.purchase_inventory.term.general_ledeger_account,
                    date = date ,
                    balance=  balance ,
                    transaction_type="Debit" , 
                    comment=f"return {inventory_return.num_returned} from {inventory_return.inventory_price.inventory} to {inventory_return.inventory_price.purchase_inventory.supplier}")
        transaction2.save()
      
    def vaildate_return(self , request,   obj):
        """
        # num of returned unit can't be greater than num units purchased
        a custom vaildation as we can't do that in the level of model of form using clean method
        as the failed inventory_price we don't render it and save it's manually
        """
        if obj.inventory_price.inventoryreturn_set.exists():
            agg_data =obj.inventory_price.inventoryreturn_set.aggregate(total_num_returned=Sum("num_returned"))
            avilable = obj.inventory_price.number_of_unit - agg_data.get("total_num_returned", 0)
            if obj.num_returned > avilable:
                messages.info(request, f"num of returned unit {obj.num_returned} can't be greater than num units purchase take into our account previous returned: {avilable}")
                return False

        else:
            if obj.num_returned > obj.inventory_price.number_of_unit:
                messages.info(request, f"num of returned unit {obj.num_returned} can't be greater than num units purchase {obj.inventory_price.number_of_unit}")
                return False

    def get(self,request,*args, **kwargs):
        form = InventoryReturnForm()
        return render(request , self.template_name , {"form": form} )

    def post(self, request, pk , *args, **kwargs):
        owner = request.user
        query = get_object_or_404(InventoryPrice , pk=pk , inventory__owner=owner)
        form = InventoryReturnForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.inventory_price = get_object_or_404(InventoryPrice , pk=pk , inventory__owner=owner)
            if self.vaildate_return(request , obj) == False:
                return render(request , self.template_name , {"form": form} )
            obj.save()
            purchaseinventory = obj.inventory_price.purchase_inventory
            purchaseinventory.status = 0 if purchaseinventory.check_status() =="UNPAID" else 1
            purchaseinventory.num_returend , purchaseinventory.cost_returned =  purchaseinventory.check_num_cost_of_returned_inventory()
            purchaseinventory.net_purchases = purchaseinventory.check_net_purchase()
            # purchaseinventory.total_amount_paid
            purchaseinventory.save()

            self.save_journal_transaction(owner=owner, inventory_return= obj)
            return redirect(reverse_lazy(self.success_url , args=[
                query.inventory.pk
            ]))
        return render(request , self.template_name , {"form": form} )

    
class ListPurchaseInventoryView(OwnerListView):
    model = PurchaseInventory
    template_name = "inventory/purchase_list.html"
    paginate_by = 30
    ordering = ["-purchase_date"]


class DetailPurchaseInventoryView(OwnerDetailView):
    model = PurchaseInventory
    template_name = "inventory/purchase_detail.html"
    

class PurchasesDashboard(LoginRequiredMixin , View):
    template_name = "inventory/purchases_dashboard.html"
    def get(self , request , *args, **kwargs):
        owner = request.user

        initial_data = {
            "start_date": None , 
            "end_date": None}
        try:
            initial_data["start_date"] =  PurchaseInventory.objects.filter(owner=owner).earliest("purchase_date").purchase_date
            initial_data["end_date"] =  PurchaseInventory.objects.filter(owner=owner).latest("purchase_date").purchase_date
        except PurchaseInventory.DoesNotExist:
            pass
        reporting_period_form = ReportingPeriodConfigForm(initial = initial_data)

        # summary_supplier = PurchaseInventory.purchases.group_by_supplier(owner)
        # summary_supplier_df = pd.DataFrame(summary_supplier)

        data = PurchaseInventory.purchases.join_data(owner.id)
        data_coulumns = [
                'pu.id' ,
                'pu.owner_id' ,
                'pu.purchase_date',
                'pu.frieght_in' ,
                'pr.number_of_unit' ,
                'pr.cost_per_unit' ,
                'Re.date' , 
                're.num_returned',
                'pa.amount_paid' ,
                'su.first_name' ,
                'su.middle_name' ,
                'su.last_name' ,
                'inv.item_name' ,
                'acc.account' , 
                'te.config' ,
                'te.terms' ,
                'te.discount_percentage' ,
                'te.discount_in_days' ,
                'te.num_of_days_due' 
        ]
        df = pd.DataFrame(data, columns=data_coulumns)
        df["total_cost"] = df["pr.number_of_unit"] * df["pr.cost_per_unit"] 
        df["total_cost_returned"] = df["re.num_returned"] * df["pr.cost_per_unit"] 
        df = df.sort_values('pr.number_of_unit').reset_index()


        # plt.switch_backend("AGG")
        # fig, ax1 = plt.subplots(figsize=(11.5, 5))
        # sns.barplot(x="net_pruchases", y="Supplier", data=summary_supplier_df.sort_values("net_pruchases" , ascending=False) , color="blue" , label="net purchases")
        # sns.barplot(x="total_amount_unpaid", y="Supplier", data=summary_supplier_df , color="red" , label="UNPAID amount")
        # plt.yticks(rotation=45)
        # plt.legend()
        # plt.xlabel("total amount")
        # plt.title("Supplier Vs Purchases Vs UNPAID amount")
        # graph = get_graph()

        plt.switch_backend("AGG")
        fig, ax1 = plt.subplots(figsize=(11.5, 5))
        sns.lineplot(data=df, x="pu.purchase_date" , y="total_cost" , color="blue" , label="total cost of purchases")
        sns.lineplot(data=df, x="pu.purchase_date" , y="total_cost_returned" , color="red" , label="total cost of returnd")
        plt.ylabel("Total")
        plt.xlabel("Date")
        plt.title("Purchases and Returnning over the time")
        graph2 = get_graph()

        plt.switch_backend("AGG")
        fig, ax1 = plt.subplots(figsize=(11.5, 5))
        sns.barplot(x="pr.number_of_unit", y="inv.item_name", data=df.sort_values("pr.number_of_unit" , ascending=False) , color="blue" , label="Num of unit" )
        sns.barplot(x="re.num_returned", y="inv.item_name", data=df.sort_values("pr.number_of_unit" , ascending=False) , color="red" , label="Num of returned")
        plt.title("inventory item")
        plt.xlabel("Number of unit")
        plt.ylabel("inventoy")
        plt.yticks(rotation=45)
        plt.legend()
        graph3 = get_graph()
    

        query = Q(owner=owner)    
        ctx = {
            "form": reporting_period_form,
            "total_purchases_amount" : PurchaseInventory.purchases.total_purchases_amount(query) , 
            "avg_cost_per_unit": PurchaseInventory.purchases.avg_cost_per_unit(query) , 
            # "avg_cost_per_unit": PurchaseInventory.purchases.avg_cost_per_unit(query) , 
            # "std_cost_per_unit": PurchaseInventory.purchases.std_cost_per_unit(query) , 
            # "max_cost_per_unit": PurchaseInventory.purchases.max_cost_per_unit(query) , 
            # "min_cost_per_unit": PurchaseInventory.purchases.min_cost_per_unit(query) , 
            "total_units_returned": PurchaseInventory.purchases.total_units_returned(query) , 
            # "total_cost_of_units_returned": PurchaseInventory.purchases.total_cost_of_units_returned(query) ,
            "net_purchases": PurchaseInventory.purchases.net_purchases(query) , 
            # "total_amount_unpaid": PurchaseInventory.purchases.total_amount_unpaid(query) , 
            "total_amount_paid": PurchaseInventory.purchases.total_amount_paid(query) , 
            # "graph": graph,
            "line_fig": graph2 ,
            "graph3" : graph3
 

        }

        return render(request , self.template_name , ctx)
        
class PayInvoicePayView(OwnerCreateView):
    form_class = PayInvoiceForm
    template_name = "inventory/payinvoice_form.html"

    def get_initial(self):
        try:
            invoice = PurchaseInventory.objects.get(owner=self.request.user , pk=self.kwargs['pk'] , status=0)
            return {'purchase_inventory': invoice}
        except PurchaseInventory.DoesNotExist:
            messages.warning(self.request , "Warning:the pk in your url is not vaild.") 

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"owner":self.request.user})
        return kwargs
