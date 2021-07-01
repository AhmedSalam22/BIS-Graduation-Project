from django.shortcuts import render , redirect , get_object_or_404 
from django.urls import reverse_lazy
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView , OwnerDetailView
from inventory.models import PaymentSalesTerm , Inventory , InventoryReturn , InventoryPrice , PurchaseInventory, PayInvoice, InventoryImag
from django.views.generic import View , TemplateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.forms import ( PaymentSalesTermForm , PurchaseInventoryForm , InventoryPriceFormset ,
    InventoryPriceFormsetHelper , InventoryReturnForm , PayInvoiceForm  , ReportingPeriodConfigForm,
    PurchaseFilter, InventoryForm, ImageFormest,ImageFormsetHelper, ImageFormSet, InventoryAllowanceForm
    )
from sole_proprietorship.models import Journal, Accounts
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum , Q
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django_filters.views import FilterView
from inventory.crispy_forms import PurchaseFilterHelper, InventoryFilterHelper
from django.db import transaction
from inventory.filter_forms import InventoryFilter
from django.core import serializers

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

class FilterContextMixin:
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['helper'] = self.helper
        return ctx

class FormKwargsMixin:
    def get_form_kwargs(self):
        """override get_form_kwargs from CREATE or UPDATE View to accept owner as argument"""
        kwargs = super().get_form_kwargs()
        kwargs.update({"owner":self.request.user})
        return kwargs

class CreateTermView(FormKwargsMixin, OwnerCreateView):
    form_class  = PaymentSalesTermForm
    template_name = "inventory/term_form.html"


class UpdateTermView(FormKwargsMixin, OwnerUpdateView):
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

    @transaction.atomic
    def post(self , request , *args , **kwargs):
        """
            save the form data if is vaild
        """
        owner = self.request.user
        purchase_inventory_form = PurchaseInventoryForm(data=request.POST , owner=owner)
        inventory_price_formset = InventoryPriceFormset(request.POST , form_kwargs={'owner': owner})
        if purchase_inventory_form.is_valid() and inventory_price_formset.is_valid():
            purchase_inventory = purchase_inventory_form.save(commit=False)
            purchase_inventory.owner = owner
            purchase_inventory.due_date = purchase_inventory.check_due_date()

            purchase_inventory.status = 0 if purchase_inventory.check_status() =="UNPAID" else 1 
            purchase_inventory.save()
    
            for form in inventory_price_formset:
                inventory_price = form.save(commit=False)
                inventory_price.purchase_inventory = purchase_inventory
                inventory_price.save()
            
            messages.success(request, 'Your Purchase has been created Successfuly')
            return redirect(reverse_lazy(self.success_url , args=[
                purchase_inventory.pk
            ]))
        ctx = {
                    "purchase_inventory_form":purchase_inventory_form,
                    "inventory_price_formset":inventory_price_formset,
                    "inventory_price_formset_helper": self.inventory_price_formset_helper,
                }
        return render(request , self.template_name , ctx )


class CreateInventoryView(LoginRequiredMixin, View):

    template_name = 'inventory/inventory_create.html'
    success_url = None
    imageHelper =  ImageFormsetHelper()
    
    def get(self, request, *args, **kwargs):
        inventoryForm, imageFormset = InventoryForm() ,  ImageFormest()
        inventoryForm.fields['general_ledeger_account'].queryset = Accounts.objects.filter(owner= request.user).all()
        ctx = {
            'inventoryForm': inventoryForm,
            'imageFormset': imageFormset, 
            'imageHelper': self.imageHelper
        }
        return render(request, self.template_name, ctx)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        inventoryForm, imageFormset = InventoryForm(request.POST) ,  ImageFormest(request.POST, request.FILES)
        if inventoryForm.is_valid() and imageFormset.is_valid():
            inventory = inventoryForm.save(commit=False)
            inventory.owner = request.user
            inventory.save()
            for imageForm in imageFormset:
                image = imageForm.save(commit=False)
                print("img",image.img)
                image.inventory = inventory
                image.save()
            messages.success(request, 'Your Inventory has been created Successfuly')
            return redirect(reverse_lazy(self.success_url , args=[
                inventory.pk
            ]))
        return (request, self.template_name, {
            'inventoryForm': inventoryForm,
            'imageFormset': imageFormset,
            'imageHelper': self.imageHelper

        })



class UpdateInventoryView(LoginRequiredMixin, View):
    template_name = 'inventory/inventory_create.html'
    success_url = None
    imageHelper =  ImageFormsetHelper()

    def get(self, request, pk, *args, **kwargs):
        inventory = get_object_or_404(Inventory, pk=pk, owner=request.user)
        inventoryForm, imageFormset = InventoryForm(instance=inventory) ,  ImageFormSet(instance=inventory)
        inventoryForm.fields['general_ledeger_account'].queryset = Accounts.objects.filter(owner= request.user).all()
        ctx = {
            'inventoryForm': inventoryForm,
            'imageFormset': imageFormset, 
            'imageHelper': self.imageHelper
        }
        return render(request, self.template_name, ctx)

    def post(self, request, pk,  *args, **kwargs):

        inventory = get_object_or_404(Inventory, pk=pk, owner=request.user)
        inventoryForm, imageFormset = InventoryForm(request.POST, instance=inventory) ,  ImageFormSet(request.POST, request.FILES, instance=inventory)
        if inventoryForm.is_valid() and imageFormset.is_valid():
            inventory = inventoryForm.save(commit=False)
            inventory.owner = request.user
            inventory.save()
            for imageForm in imageFormset:
                image = imageForm.save(commit=False)
                print("img",image.img)
                if image.img != None:
                    image.inventory = inventory
                    image.save()
            messages.success(request, 'Your Inventory has been updated Successfuly')
            return redirect(reverse_lazy(self.success_url , args=[
                inventory.pk
            ]))
        return (request, self.template_name, {
            'inventoryForm': inventoryForm,
            'imageFormset': imageFormset,
            'imageHelper': self.imageHelper

        })

class ListInventoryView(LoginRequiredMixin, FilterContextMixin, FilterView):
    model = Inventory
    template_name = "inventory/inventory_list.html"
    paginate_by = 20
    ordering = ['item_name']
    filterset_class = InventoryFilter
    helper = InventoryFilterHelper()


    def get_queryset(self):
        qs = super().get_queryset().filter(owner= self.request.user)
        # selected related used to cash the result from FK without hit the database
        return qs


    
class DetailInventoryView(OwnerDetailView):
    model = Inventory
    template_name = "inventory/inventory_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["last_unit"] =  context["inventory"].inventoryprice_set.order_by("-purchase_inventory__purchase_date").first()
        # prices >> all the hisorcal data for purchases
        context["prices"] = context["inventory"].inventoryprice_set.order_by("-purchase_inventory__purchase_date").select_related()
        return context
    


class DeleteInventoryView(OwnerDeleteView):
    model = Inventory

class HomeView(TemplateView):
    template_name = "inventory/index.html"


class CreatePurchaseReturnView(LoginRequiredMixin ,View):
    template_name = "inventory/purchase_return_form.html"
    success_url = "inventory:detail_inventory"

    def get(self,request,*args, **kwargs):
        form = InventoryReturnForm()
        form.fields['inventory_price'].queryset = InventoryPrice.objects.filter(inventory__owner=request.user).all()
        if kwargs.get('pk', None) != None: 
            inventory_price = get_object_or_404(InventoryPrice , pk=kwargs.get('pk') , inventory__owner=request.user)
            form.fields['inventory_price'].initial = inventory_price
        
        return render(request , self.template_name , {"form": form} )

    @transaction.atomic
    def post(self, request, pk , *args, **kwargs):
        owner = request.user
        query = get_object_or_404(InventoryPrice , pk=pk , inventory__owner=owner)
        form = InventoryReturnForm(data=request.POST)
        if form.is_valid():
            obj = form.save(commit=True)
            return redirect(reverse_lazy(self.success_url , args=[
                obj.inventory_price.inventory.pk
            ]))
        return render(request , self.template_name , {"form": form} )

    
class ListPurchaseInventoryView(LoginRequiredMixin, FilterContextMixin, FilterView):
    model = PurchaseInventory
    template_name = "inventory/purchase_list.html"
    paginate_by = 30
    ordering = ["-purchase_date"]
    filterset_class = PurchaseFilter
    helper = PurchaseFilterHelper()

    def get_queryset(self):
        qs = super().get_queryset().filter(owner=self.request.user).all()
        print('query', qs.query)
        return qs


class DetailPurchaseInventoryView(OwnerDetailView):
    model = PurchaseInventory
    template_name = "inventory/purchase_detail.html"


    


class DeletePurchaseInventoryView(OwnerDeleteView):
    model = PurchaseInventory

class PurchasesDashboard(LoginRequiredMixin , View):
    template_name = "inventory/purchases_dashboard.html"
    def get(self , request , *args, **kwargs):
        owner = request.user

        initial_data = {
            "start_date": timezone.now() - timezone.timedelta(weeks=1) , 
            "end_date": timezone.now() }
  
        reporting_period_form = ReportingPeriodConfigForm(initial = initial_data)

        start_date = request.GET.get("start_date", initial_data["start_date"])
        end_date = request.GET.get("end_date", initial_data["end_date"])
        query = Q(owner=owner) & Q(purchase_date__gte=start_date)  & Q(purchase_date__lte=end_date)

        data = PurchaseInventory.purchases.analysis(owner.id , start_date , end_date)
        purchases_return_over_time_df = pd.DataFrame(data["purchases_return_over_time"] , columns=["purchase_date" , "net_purchases" , "cost_returned"])
        inventory_df = pd.DataFrame(data["inventory"] , columns=["item_name", "number_of_unit" , "num_returned"])
        summary_supplier_df = pd.DataFrame(data["supplier"] , columns=["supplier", "total_purchases" , "cost_returned" ])

    

        plt.switch_backend("AGG")
        fig, ax1 = plt.subplots(figsize=(11.5, 5))
        try:
            sns.barplot(x="total_purchases", y="supplier", data=summary_supplier_df , color="blue" , label="total purchases")
            sns.barplot(x="cost_returned", y="supplier", data=summary_supplier_df , color="red" , label="cost_returned")
        except ValueError:
            pass

        plt.yticks(rotation=45)
        plt.legend()
        plt.xlabel("total amount")
        plt.title("Supplier Vs total purchases  Vs cost of returned")
        graph = get_graph()
   
    
        
        plt.switch_backend("AGG")
        fig, ax1 = plt.subplots(figsize=(11.5, 5))
        try:
            sns.lineplot(data=purchases_return_over_time_df, x="purchase_date" , y="net_purchases" , color="blue" , label="total cost of purchases")
            sns.lineplot(data=purchases_return_over_time_df, x="purchase_date" , y="cost_returned" , color="red" , label="total cost of returnd")
        except ValueError:
            pass
        plt.ylabel("Total")
        plt.xlabel("Date")
        plt.title("Purchases and Returnning over the time")
        graph2 = get_graph()
        

        plt.switch_backend("AGG")
        fig, ax1 = plt.subplots(figsize=(11.5, 5))
        try:
            sns.barplot(x="number_of_unit", y="item_name", data=inventory_df , color="blue" , label="Num of unit" )
            sns.barplot(x="num_returned", y="item_name", data=inventory_df , color="red" , label="Num of returned")
        except ValueError:
            pass 
        plt.title("inventory item")
        plt.xlabel("Number of unit")
        plt.ylabel("inventoy")
        plt.yticks(rotation=45)
        plt.legend()
        graph3 = get_graph()

    


        ctx = {
            "start_date": start_date ,
            "end_date": end_date ,
            "form": reporting_period_form,
            "purchases_analysis": PurchaseInventory.purchases.purchases_analysis(query) , 
            # "avg_cost_per_unit": PurchaseInventory.purchases.avg_cost_per_unit(query) , 
            # "avg_cost_per_unit": PurchaseInventory.purchases.avg_cost_per_unit(query) , 
            # "std_cost_per_unit": PurchaseInventory.purchases.std_cost_per_unit(query) , 
            # "max_cost_per_unit": PurchaseInventory.purchases.max_cost_per_unit(query) , 
            # "min_cost_per_unit": PurchaseInventory.purchases.min_cost_per_unit(query) , 
            "graph": graph,
            "line_fig": graph2 ,
            "graph3" : graph3
 

        }

        return render(request , self.template_name , ctx)
        
class PayInvoicePayView(FormKwargsMixin, OwnerCreateView):
    form_class = PayInvoiceForm
    template_name = "inventory/payinvoice_form.html"

    def get_initial(self):
        try:
            invoice = PurchaseInventory.objects.get(owner=self.request.user , pk=self.kwargs['pk'] , status=0)
            return {'purchase_inventory': invoice}
        except PurchaseInventory.DoesNotExist:
            messages.warning(self.request , "Warning:the pk in your url is not vaild.") 

    @transaction.atomic
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)



class PayInvoiceDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'inventory/pay_invoice_delete.html'
    model = PayInvoice

    def get_queryset(self):
        qs = super().get_queryset().filter(purchase_inventory__owner=self.request.user).distinct()
        return qs



class PivotTableView(LoginRequiredMixin , View):
    template_name = "inventory/pivot_table.html"
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class PurchaseAllowanceView(LoginRequiredMixin, View):
    template_name = 'inventory/purchase_allowance_form.html'
    success_url = None

    def get(self, request, *args, **kwargs):
        form = InventoryAllowanceForm()
        form.fields['purchase_inventory'].queryset = PurchaseInventory.objects.filter(owner=request.user).all()
        form.fields['purchase_inventory'].initial = PurchaseInventory.objects.filter(owner=request.user, pk= kwargs.get('pk', None)).first()
        
        if kwargs.get('pk', None) != None:
            purchase =  get_object_or_404(PurchaseInventory, owner=request.user, pk= kwargs['pk'])
            form.fields['inventory_price'].queryset =  InventoryPrice.objects.filter(purchase_inventory=purchase)
        else:
            purchase =  PurchaseInventory.objects.filter(owner=request.user).first()
            form.fields['inventory_price'].queryset =  InventoryPrice.objects.none()
        ctx = {
            'form': form
        }
        return render(request, self.template_name, ctx)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = InventoryAllowanceForm(request.POST)
        if form.is_valid():
            obj = form.save()
            messages.success(request, 'Your Allowance has been created Successfuly')
            return redirect(reverse_lazy(self.success_url , args=[
                obj.purchase_inventory.pk
            ]))
        return render(request , self.template_name , {"form": form} ) 



class FetchInventoryPriceView(LoginRequiredMixin , View):
    def get(self, request, *args, **kwargs):
        inventory_prices = InventoryPrice.objects.select_related('inventory').filter(purchase_inventory__owner= request.user,
                            purchase_inventory=request.GET.get('purchase_inventory')
                            ).distinct().values('pk', 'inventory__item_name', 'cost_per_unit')

        return JsonResponse(
                 list(inventory_prices), safe = False
            )


class Test(LoginRequiredMixin , View):


    def get(self , request , *args , **kwargs):
        import json

        initial_data = {
        "start_date": timezone.now() - timezone.timedelta(weeks=10) , 
        "end_date": timezone.now() 
        }
  

        start_date = request.GET.get("start_date", initial_data["start_date"])
        end_date = request.GET.get("end_date", initial_data["end_date"])

        data = PurchaseInventory.purchases.analysis(request.user.id , start_date , end_date)
        # df = pd.DataFrame(data["purchases_return_over_time"] , columns=["purchase_date" , "net_purchases" , "cost_returned"])
        df = pd.DataFrame(data["supplier"] , columns=["supplier", "total_purchases" , "cost_returned" ])

        response = HttpResponse(content_type='application/json')
        # response['Content-Disposition'] = 'attachment; filename="somefilename.json"'
        df.to_json(response, orient='records')

        return response