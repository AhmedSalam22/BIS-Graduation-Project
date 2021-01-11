from django.shortcuts import render
from home.owner import OwnerCreateView ,OwnerDeleteView , OwnerListView , OwnerUpdateView
from inventory.models import PaymentSalesTerm
# Create your views here.

class CreateTermView(OwnerCreateView):
    model = PaymentSalesTerm
    fields = ['config' , 'terms' , 'num_of_days_due' , 'discount_in_days' , 'discount_percentage' ]
    template_name = "inventory/term_form.html"

class UpdateTermView(OwnerUpdateView):
    model = PaymentSalesTerm
    fields = ['config' , 'terms' , 'num_of_days_due' , 'discount_in_days' , 'discount_percentage' ]
    template_name = "inventory/term_form.html"


class ListTermView(OwnerListView):
    model = PaymentSalesTerm
    template_name = "inventory/term_list.html"
    paginate_by = 5
    ordering = ["config"]

class DeleteTermView(OwnerDeleteView):
    model = PaymentSalesTerm
    template_name = "inventory/term_delete.html"