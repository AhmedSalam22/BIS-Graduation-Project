from django.shortcuts import render
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView
from inventory.models import PaymentSalesTerm
from django.views.generic import View
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

    def get(self , request , *args, **kwargs):
        owner = self.request.user
        purchase_inventory_form = PurchaseInventoryForm(owner)
        inventory_price_formset = InventoryPriceFormset(form_kwargs={'owner': owner})
        inventory_price_formset_helper = InventoryPriceFormsetHelper()

        ctx = {
            "purchase_inventory_form":purchase_inventory_form,
            "inventory_price_formset":inventory_price_formset,
            "inventory_price_formset_helper":inventory_price_formset_helper,
        }
        return render(request , self.template_name , ctx )