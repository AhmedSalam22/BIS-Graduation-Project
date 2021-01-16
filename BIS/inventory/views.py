from django.shortcuts import render , redirect
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView , OwnerDetailView
from inventory.models import PaymentSalesTerm , Inventory
from django.views.generic import View , TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from inventory.forms import PaymentSalesTermForm , PurchaseInventoryForm , InventoryPriceFormset , InventoryPriceFormsetHelper
from sole_proprietorship.models import Journal
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
        context["prices"] = context["inventory"].inventoryprice_set.order_by("-purchase_inventory__purchase_date")
        return context
    

class HomeView(TemplateView):
    template_name = "inventory/index.html"