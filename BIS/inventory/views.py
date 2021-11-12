from django.shortcuts import render , redirect , get_object_or_404 
from django.urls import reverse_lazy
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView , OwnerDetailView
from inventory.models import (PaymentSalesTerm , Inventory , InventoryReturn , InventoryPrice,
    PurchaseInventory, PayInvoice, InventoryImag, Sold_Item, Sale, SalesReturn, SalesAllowance
    )
from django.views.generic import View , TemplateView, DeleteView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.forms import ( PaymentSalesTermForm , PurchaseInventoryForm , InventoryPriceFormset ,
    InventoryPriceFormsetHelper , InventoryReturnForm , PayInvoiceForm  , ReportingPeriodConfigForm,
    PurchaseFilter, InventoryForm, ImageFormest,ImageFormsetHelper, ImageFormSet, InventoryAllowanceForm,
    SalesForm, SoldItemFormset, SalesReturnForm, SalesAllowaceForm, SalesPaymentForm, SalesFilterForm,
    SalesAllowanceFormSet

    )
from sole_proprietorship.models import Journal, Accounts
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Q, F, FloatField, ExpressionWrapper, Case, When, Value,IntegerField
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django_filters.views import FilterView
from inventory.crispy_forms import (PurchaseFilterHelper, InventoryFilterHelper, SalesFormsetHelper,
    SalesAllowanceFormSetHelper
)
from django.db import transaction
from inventory.filter_forms import InventoryFilter
from django.core import serializers
import plotly.graph_objects as go
import plotly
import plotly.express as px
import plotly.figure_factory as ff
from django.db.models.functions import Coalesce, ExtractDay, Concat, Now, Cast, TruncDate
from django.db.models import Func, DateTimeField, CharField, DateField 
from django.utils.functional import cached_property
from django.db.models.expressions import RawSQL

class DaysInterval(Func):
    function = 'make_interval'
    template = '%(function)s(days:=%(expressions)s)'

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



class CreateSalesView(LoginRequiredMixin, View):
    template_name = "inventory/sales_form.html"
    success_url = None
    salesFormsetHelper = SalesFormsetHelper()

    def get(self, request, *args, **kwargs):
        sales_form = SalesForm(owner=request.user)
        sold_item_formset = SoldItemFormset(form_kwargs = {'owner_id': request.user.id})

        ctx = {
            'sales_form': sales_form, 
            'salesFormsetHelper': self.salesFormsetHelper,
            'sold_item_formset': sold_item_formset
        }

        return render(request, self.template_name, ctx)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        sales_form = SalesForm(data= request.POST, owner=request.user)
        sold_item_formset = SoldItemFormset(data= request.POST, form_kwargs = {'owner_id': request.user.id})
        if sales_form.is_valid() and sold_item_formset.is_valid():
            sales = sales_form.save(commit=False)
            sales.owner = request.user
            sales.save()
            for sold_item_form in sold_item_formset:
                sold_item = sold_item_form.save(commit=False)
                sold_item.sale = sales
                sold_item.save()
            messages.success(request, 'Your Sales has been created Successfuly')
            return redirect(
                reverse_lazy('inventory:sale_detail', args=[sales.id])
                )
        ctx = {
            'sales_form': sales_form, 
            'salesFormsetHelper': self.salesFormsetHelper,
            'sold_item_formset': sold_item_formset
        }
        return render(request , self.template_name , ctx )





class CreatePurchaseInventoryView(LoginRequiredMixin, View):
    template_name = "inventory/purchase_form.html"
    success_url = None
    inventory_price_formset_helper = InventoryPriceFormsetHelper()
        
    def get(self , request , *args, **kwargs):
        owner = request.user
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
        qs = super().get_queryset().prefetch_related('imgs').filter(owner= self.request.user)
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
        form.fields['inventory_price'].queryset = InventoryPrice.objects.filter(inventory__owner=request.user).select_related('inventory')
        if kwargs.get('pk', None) != None: 
            inventory_price = get_object_or_404(InventoryPrice , pk=kwargs.get('pk') , inventory__owner=request.user)
            form.fields['inventory_price'].initial = inventory_price
        
        return render(request , self.template_name , {"form": form} )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        owner = request.user
        query = get_object_or_404(InventoryPrice , pk=kwargs.get('pk')  , inventory__owner=owner)
        form = InventoryReturnForm(data=request.POST)
        if form.is_valid():
            obj = form.save(commit=True)
            return redirect(reverse_lazy(self.success_url , args=[
                obj.inventory_price.inventory.pk
            ]))
        return render(request , self.template_name , {"form": form} )


class CreateSalesReturnView(LoginRequiredMixin , View):
    template_name = 'inventory/sales_return_form.html'



    def get(self, request, *args, **kwargs):
        form = SalesReturnForm(sales_pk=kwargs.get('sales_pk'), sales_item_pk=kwargs.get('sales_item_pk'), owner=request.user)
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = SalesReturnForm(data= request.POST, owner=request.user)        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Sales return has been created Successfuly')
            return redirect(reverse_lazy('inventory:home'))
        return render(request, self.template_name, {'form': form})




class ListPurchaseInventoryView(LoginRequiredMixin, FilterContextMixin, FilterView):
    model = PurchaseInventory
    template_name = "inventory/purchase_list.html"
    paginate_by = 30
    ordering = ["-purchase_date"]
    filterset_class = PurchaseFilter
    helper = PurchaseFilterHelper()

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            'supplier', 'term', 
        ).filter(owner=self.request.user).all()
        print('query', qs.query)
        return qs


class DetailPurchaseInventoryView(OwnerDetailView):
    model = PurchaseInventory
    template_name = "inventory/purchase_detail.html"


    


class DeletePurchaseInventoryView(OwnerDeleteView):
    model = PurchaseInventory



class Dash:
    start_date = (timezone.now() - timezone.timedelta(weeks=4)).date()
    end_date = timezone.now().date()

    def __init__(self, owner_id):
        self.owner_id = owner_id

    @cached_property
    def num_sales(self):
        return Sale.objects.filter(owner__id= self.owner_id, sales_date__gte= Dash.start_date, sales_date__lte= Dash.end_date).count()

    @property
    def sold_item_filter(self):
        return (
                Q(sale__owner__id = self.owner_id) & Q(sale__sales_date__gte= Dash.start_date) & Q(sale__sales_date__lte= Dash.end_date)
            )

    @cached_property
    def total_sales(self):
        query = Sold_Item.objects.filter(
            self.sold_item_filter
        ).annotate(
            total = (F('sale_price') * F('quantity'))
        ).aggregate(
            total_sales_amount = Sum('total')
        )
        return query['total_sales_amount'] if query['total_sales_amount'] != None else 0


    @cached_property
    def sales_return_amt(self):
        query = SalesReturn.objects.filter(
            self.sold_item_filter
        ).annotate(
            total=ExpressionWrapper( 
                (F('sold_item__sale_price') * F('num_returned')),
                output_field = FloatField()
            )
        ).aggregate(
            total_sales_return_amt = Sum('total')
        )
        return query['total_sales_return_amt'] if query['total_sales_return_amt'] != None else 0

    @cached_property
    def sales_return_unit(self):
        query = SalesReturn.objects.filter(
            self.sold_item_filter
        ).aggregate(
            num_returned=Sum('num_returned')
        )
        return query['num_returned'] if query['num_returned'] != None else 0

    @cached_property
    def sales_allowance(self):
        filter_expression = ( 
            Q(sales__owner__id = self.owner_id) & Q(sales__sales_date__gte= Dash.start_date) & Q(sales__sales_date__lte= Dash.end_date)
        )
        query = SalesAllowance.objects.filter(
            filter_expression
        ).aggregate(
            sales_allowance=Sum('amount')
        )
        return query['sales_allowance'] if query['sales_allowance'] != None else 0

    @cached_property
    def net_sales(self):
        return self.total_sales - self.sales_return_amt - self.sales_allowance

    @cached_property
    def money_recieved(self):
        # query one ignore if it's already pay in cash
        query = Sale.sales.all_sales(owner_id=self.owner_id).filter(
            sales_date__gte= Dash.start_date , sales_date__lte= Dash.end_date
            ).aggregate(
                money_revieved=Coalesce(Sum('total_amt_paid', output_field=FloatField()),0.0)
            )
        # to avoid the above issue
        query2 = Sale.sales.all_sales(
            owner_id=self.owner_id
            ).filter(
                term__terms = PaymentSalesTerm.Term.CASH.value
            ).aggregate(
                money_revieved=Coalesce(Sum('netsales'), 0.0)
            )

        return query['money_revieved'] + query2['money_revieved']


    @cached_property
    def num_unpaid_invoice(self):
        return Sale.sales.all_sales(owner_id=self.owner_id).filter(status="UNPAID",  sales_date__gte= Dash.start_date , sales_date__lte= Dash.end_date).count()
    
    @cached_property
    def amount_unpaid_sales(self):
        return self.net_sales - self.money_recieved
           
    
    @cached_property
    def aged_receivables(self):
        """
          0-30
          31-60
          61-90
          over 90 days
        """
        result = dict()
        aged_receivables = ['0-30', '31-60', '61-90', 'over 90 days']

        query = Sale.sales.all_sales(self.owner_id).filter(status='UNPAID', sales_date__gte= Dash.start_date , sales_date__lte= Dash.end_date).annotate(
            days_overdue=  ExtractDay(timezone.now().date() - F('due_date')) ,
            aged_receivables=Case(
                When(days_overdue__lte = 30, then=Value('0-30')),
                When(days_overdue__lte = 60, then=Value('31-60')),
                When(days_overdue__lte = 90, then=Value('61-90')),
                When(days_overdue__gt = 90, then=Value('over 90 days')),
                output_field= CharField(max_length=50)
            )
        )
        for age_receivable in aged_receivables:
            result[age_receivable] = query.filter(aged_receivables=age_receivable).aggregate(total_amt_unpaid__sum=Coalesce(Sum('total_amt_unpaid'), 0.0))['total_amt_unpaid__sum']
        return result
        
    @property
    def aged_receivables_pie_tbl_chart(self):
        data = self.aged_receivables
        data_matrix = [
                        ['Aged Receivables', 'total amout unpaid', '%']
                    ]
        TOTAL_AMT_UNPAID = sum(list(data.values())) or 1
        for key, value in data.items():
            data_matrix.append([key, value, round(value/TOTAL_AMT_UNPAID *100, 2)])

        data_matrix.append(['TOTAL', TOTAL_AMT_UNPAID, '100%'])

        fig_tbl = ff.create_table(data_matrix)
        fig_pie = go.Figure(data=[go.Pie(labels=list(data.keys()), values= list(data.values()))] )
        fig_pie.update_layout(title_text= 'Aged Receivables')
        return fig_pie.to_html(full_html=False, include_plotlyjs=False),  fig_tbl.to_html(full_html=False, include_plotlyjs=False)

    
   
    @cached_property
    def customers_who_owe_money(self):
        query = Sale.sales.all_sales(self.owner_id).filter(
            status='UNPAID',
            sales_date__gte= Dash.start_date ,
            sales_date__lte= Dash.end_date
            ).values('customer_id','customer_name', 'total_amt_unpaid')

        df = pd.DataFrame(query)
        try:
            return df.groupby(['customer_id', 'customer_name']).agg(['sum', 'count']).reset_index().to_html(index=False, classes="table table-hover table-borderless datatable")
        except KeyError:
            return df.to_html(index=False, classes="table table-hover table-borderless datatable")





    @staticmethod
    def reporting_period_form():
        initial_data =  {"start_date": Dash.start_date,  "end_date": Dash.end_date}
        return ReportingPeriodConfigForm(initial= initial_data)

class PurchasesDashboard(LoginRequiredMixin , View):
    template_name = "inventory/purchases_dashboard.html"
    def get(self , request , *args, **kwargs):
        owner = request.user

        reporting_period_form = Dash.reporting_period_form()

        start_date = request.GET.get("start_date", Dash.start_date)
        end_date = request.GET.get("end_date", Dash.end_date)

        query = Q(owner=owner) & Q(purchase_date__gte=start_date)  & Q(purchase_date__lte=end_date)

        data = PurchaseInventory.purchases.analysis(owner.id , start_date , end_date)
        purchases_return_over_time_df = pd.DataFrame(data["purchases_return_over_time"] , columns=["purchase_date" , "net_purchases" , "cost_returned"])
        inventory_df = pd.DataFrame(data["inventory"] , columns=["item_name", "number_of_unit" , "num_returned"])
        summary_supplier_df = pd.DataFrame(data["supplier"] , columns=["supplier", "total_purchases" , "cost_returned" ])


        fig = go.Figure(go.Bar(
            x=summary_supplier_df['total_purchases'],
            y=summary_supplier_df['supplier'],
            name='Total Purchases',
            orientation='h'))

        fig.update_layout(title_text= 'Supplier and total purchases')
        supplier_total_purchases =  fig.to_html(full_html=False, include_plotlyjs=False)


        
        fig = go.Figure(go.Bar(
            x=summary_supplier_df['cost_returned'],
            y=summary_supplier_df['supplier'],
            name='Total Purchases',
            marker=dict(
                    color='rgba(246, 78, 139, 0.6)',
                    line=dict(color='rgba(246, 78, 139, 1.0)', width=3)
                ),
            orientation='h'))

        fig.update_layout(title_text= 'Cost returned')
        cost_returned =  fig.to_html(full_html=False, include_plotlyjs=False)

        # plt.switch_backend("AGG")
        # fig, ax1 = plt.subplots(figsize=(11.5, 5))
        # try:
        #     sns.barplot(x="total_purchases", y="supplier", data=summary_supplier_df , color="blue" , label="total purchases")
        #     sns.barplot(x="cost_returned", y="supplier", data=summary_supplier_df , color="red" , label="cost_returned")
        # except ValueError:
        #     pass

        # plt.yticks(rotation=45)
        # plt.legend()
        # plt.xlabel("total amount")
        # plt.title("Supplier Vs total purchases  Vs cost of returned")
        # graph = get_graph()
   
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(x=list(purchases_return_over_time_df.purchase_date), y=list(purchases_return_over_time_df.net_purchases))
        )

        fig.update_layout(
            title_text="Net purchases Over the time"
        )

        df_notDueAndOverDue = pd.DataFrame(
            PurchaseInventory.purchases.notDueAndOverDue(owner.id , start_date , end_date), columns=['Satus', 'Total amount unpaid', 'number']
            )
        df_notDueAndOverDue.loc[df_notDueAndOverDue.shape[0]] = ['TOTAL', df_notDueAndOverDue['Total amount unpaid'].sum(), df_notDueAndOverDue.number.sum()]
        df_fig1 = ff.create_table(df_notDueAndOverDue)
        df_fig1 = df_fig1.to_html(full_html=False, include_plotlyjs=False)


        df =  pd.DataFrame(
            PurchaseInventory.purchases.vendors_to_pay(owner.id , start_date , end_date),
            columns= ['Vendor Name', 'Amount Due', 'Open Invoices', 'Min Due Date', 'Max Due Date']
            )
        vendors_to_pay_tbl = df.to_html(index=False, justify='left', classes = "table table-hover table-borderless datatable")
        # plt.switch_backend("AGG")
        # fig, ax1 = plt.subplots(figsize=(11.5, 5))
        # try:
        #     sns.lineplot(data=purchases_return_over_time_df, x="purchase_date" , y="net_purchases" , color="blue" , label="total cost of purchases")
        #     sns.lineplot(data=purchases_return_over_time_df, x="purchase_date" , y="cost_returned" , color="red" , label="total cost of returnd")
        # except ValueError:
        #     pass
        # plt.ylabel("Total")
        # plt.xlabel("Date")
        # plt.title("Purchases and Returnning over the time")
        # graph2 = get_graph()
        

        # plt.switch_backend("AGG")
        # fig, ax1 = plt.subplots(figsize=(11.5, 5))
        # try:
        #     sns.barplot(x="number_of_unit", y="item_name", data=inventory_df , color="blue" , label="Num of unit" )
        #     sns.barplot(x="num_returned", y="item_name", data=inventory_df , color="red" , label="Num of returned")
        # except ValueError:
        #     pass 
        # plt.title("inventory item")
        # plt.xlabel("Number of unit")
        # plt.ylabel("inventoy")
        # plt.yticks(rotation=45)
        # plt.legend()
        # graph3 = get_graph()

    


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
            'supplier_total_purchases_fig': supplier_total_purchases,
            # "graph": graph,
            # "line_fig": graph2 ,
            # "graph3" : graph3,
            'cost_returned': cost_returned,
            'df_fig1': df_fig1,
            'vendors_to_pay_tbl': vendors_to_pay_tbl
 

        }

        return render(request , self.template_name , ctx)
        
class PayInvoicePayView(FormKwargsMixin, OwnerCreateView):
    form_class = PayInvoiceForm
    template_name = "inventory/payinvoice_form.html"

    def get_initial(self):
        try:
            invoice = PurchaseInventory.objects.get(owner=self.request.user , pk=self.kwargs.get('pk') , status=0)
            return {'purchase_inventory': invoice}
        except PurchaseInventory.DoesNotExist:
            pass
            # messages.warning(self.request , "Warning:the pk in your url is not vaild.") 

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


class CreateSalesAllowanceView(LoginRequiredMixin, View):
    template_name = 'inventory/sales_allowance_form.html'
    success_url = 'inventory:home'

    def get(self, request, *args, **kwargs):
        form = SalesAllowaceForm(owner=request.user, sales_pk= kwargs.get('sales_pk', None))
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = SalesAllowaceForm(data=request.POST, owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Sales Allowance has been created Successfuly')
            return redirect(reverse_lazy(self.success_url))
        return render(request , self.template_name , {"form": form} ) 





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



class FetchInventoryPriceView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        inventory_prices = InventoryPrice.objects.select_related('inventory').filter(purchase_inventory__owner= request.user,
                            purchase_inventory=request.GET.get('purchase_inventory')
                            ).distinct().values('pk', 'inventory__item_name', 'cost_per_unit')

        return JsonResponse(
                 list(inventory_prices), safe= False
            )

class FetchSoldItemView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        sold_item = Sold_Item.objects.filter(
            sale__owner__id=request.user.id,
            sale__id = request.GET.get('sale')
            ).all()
        
        return JsonResponse(
            [[item.pk, item.__str__()] for item in sold_item], safe=False
        )


class CreateSalesPaymentView(LoginRequiredMixin, View):
    template_name = 'inventory/sales_patment_form.html'

    def get(self, request, *args, **kwargs):
        form = SalesPaymentForm(owner=request.user, sales_pk=kwargs.get('sales_pk'))
        return render(request, self.template_name, {'form': form})

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = SalesPaymentForm(data= request.POST, owner=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your Payment has been created Successfuly')
            return redirect(reverse_lazy('inventory:home'))
        return render(request, self.template_name, {'form': form})


class SalesListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = "inventory/sales_list.html"
    paginate_by = 20
    ordering = ['-sales_date']


    def get_queryset(self):
        # qs = super().get_queryset().select_related(
        #     'term'
        #     ).filter(owner= self.request.user)
        qs = Sale.sales.all_sales(owner_id= self.request.user.id).select_related('term').order_by('-sales_date')
        return qs


    def get_context_data(self, *args,  **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        ctx['form'] = SalesFilterForm(self.request.GET)
        return ctx

    def filter_queryset(self, request):
        # keys = ['sales_date__gte', 'sales_date__lte', 'due_date__gte', 'due_date__lte', 'status']
        sales_filter_form = SalesFilterForm(request.GET)
        # we can't use sales_filter_form.cleaned_data unless call these method
        sales_filter_form.is_valid()
        filters = {}
        for key, value in sales_filter_form.cleaned_data.items():
            if value != "" and value != None and value != " ":
                filters[key] = value
        return filters


    def get(self, request, *args, **kwargs):
        filters = self.filter_queryset(request)
        if len(filters) == 0:
            self.object_list = self.get_queryset()
        else:
            self.object_list = self.get_queryset().filter(**filters)
        context = self.get_context_data()
        
        return self.render_to_response(context)

class SalesDeleteView(OwnerDeleteView):
    model = Sale
    

class SalesDetailView(LoginRequiredMixin, DetailView):
    model = Sale

    def get_queryset(self):
        qs = super().get_queryset().filter(owner= self.request.user).prefetch_related('sold_item_set', 'salespayment_set')
        return qs



class SalesDashboradView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/sales_dashboard.html'


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = Dash.reporting_period_form()
        if self.request.GET.get('start_date', None) != None:
            Dash.start_date = self.request.GET.get('start_date')

        if self.request.GET.get('end_date', None) != None:
             Dash.end_date = self.request.GET.get('end_date')

        ctx['start_date'], ctx['end_date'] = Dash.start_date, Dash.end_date

        dash = Dash(owner_id=self.request.user.id)
        ctx['num_sales'] = dash.num_sales
        ctx['total_sales'] = dash.total_sales
        ctx['sales_return_amt'] = dash.sales_return_amt
        ctx['sales_return_unit'] = dash.sales_return_unit
        ctx['sales_allowance'] = dash.sales_allowance
        ctx['net_sales'] = dash.net_sales
        ctx['money_recieved'] = dash.money_recieved 
        ctx['num_unpaid_invoice'] = dash.num_unpaid_invoice
        ctx['amount_unpaid_sales'] = dash.amount_unpaid_sales
        ctx['aged_receivables_pie_chart'], ctx['aged_receivables_tbl'] = dash.aged_receivables_pie_tbl_chart
        ctx['customers_who_owe_money'] = dash.customers_who_owe_money


        return ctx



class POSView(CreateSalesView):
    template_name ='inventory/post.html'




class FetchInventoryAvailableForSale(LoginRequiredMixin, View):
    SQL = """
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
            HAVING (number_of_unit - COALESCE(Sum(r.num_returned) ,0) - COALESCE(Sum(s.quantity), 0) )  > 0
         """


    def get(self, request, *args, **kwargs):
        queryset = InventoryPrice.objects.select_related(
            'inventory'
            ).prefetch_related(
                'inventory__imgs__first'
            ).filter(
                id__in =RawSQL(self.SQL, [request.user.id])
            ).distinct(
                'id', 'cost_per_unit'
                ).values(
                'id',
                'inventory__item_name',
                'cost_per_unit', 
                'inventory__description',
                'inventory__imgs__img'
            )        
        return JsonResponse(
                    [   { 
                            'id': item['id'],
                            'name': item['inventory__item_name'],
                            'description': item['inventory__description'],
                            'cost_per_unit':item['cost_per_unit'],
                            'img': item['inventory__imgs__img']
                        }

                         for item in queryset
                    ], safe=False
                )


class UpdateSalesAllowanceView(LoginRequiredMixin, View):
    template_name = 'inventory/sales_allowance_update.html'
    helper = SalesAllowanceFormSetHelper()
    message_success = 'Your Sales Allowance has been updated successfully'

    def get(self, request, sales_pk, *args, **kwargs):
        queryset = Sale.objects.filter(owner=request.user, pk=sales_pk)
        sale = get_object_or_404(queryset)
        formset = SalesAllowanceFormSet(instance=sale)
        return render(request, self.template_name, {'formset': formset, 'helper': self.helper})

    @transaction.atomic
    def post(self, request, sales_pk,  *args, **kwargs):
        queryset = Sale.objects.filter(owner=request.user, pk=sales_pk)
        sale = get_object_or_404(queryset)
        formset = SalesAllowanceFormSet(request.POST, instance=sale)
        if formset.is_valid():
            formset.save()
            messages.success(request, self.message_success)
            return redirect(
                reverse_lazy('inventory:sale_detail', args=[sales_pk])
                )
        return render(request, self.template_name, {'formset': formset, 'helper': self.helper})

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