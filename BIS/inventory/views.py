from django.shortcuts import render , redirect
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView , OwnerDetailView
from inventory.models import PaymentSalesTerm , Inventory
from django.views.generic import View , TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.forms import PaymentSalesTermForm , PurchaseInventoryForm , InventoryPriceFormset , InventoryPriceFormsetHelper

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
    ctx = None

    def get(self , request , *args, **kwargs):
        owner = self.request.user
        purchase_inventory_form = PurchaseInventoryForm(owner)
        inventory_price_formset = InventoryPriceFormset(form_kwargs={'owner': owner})

        self.ctx = {
            "purchase_inventory_form":purchase_inventory_form,
            "inventory_price_formset":inventory_price_formset,
            "inventory_price_formset_helper": self.inventory_price_formset_helper,
        }
        return render(request , self.template_name , self.ctx )

    def post(self , request , *args , **kwargs):
        owner = self.request.user
        purchase_inventory_form = PurchaseInventoryForm(data=request.POST , owner=owner)
        inventory_price_formset = InventoryPriceFormset(request.POST , form_kwargs={'owner': owner})
        if purchase_inventory_form.is_valid() and inventory_price_formset.is_valid():
            form1 = purchase_inventory_form.save(commit=False)
            form1.owner = owner
            form1.save()
            print(dir(form1))
            for form in inventory_price_formset:
                form2 = form.save(commit=False)
                form2.purchase_inventory = form1
                form2.save()

            return redirect(self.success_url)

        return render(request , self.template_name , self.ctx )

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
        context["prices"] = context["inventory"].inventoryprice_set.order_by("-purchase_inventory__purchase_date")
        return context
    

class HomeView(TemplateView):
    template_name = "inventory/index.html"