from django.shortcuts import render , reverse, redirect
from django.urls import  reverse_lazy
from .forms import CustomerForm , CustomerAddressForm , CustomerNoteForm  , CustomerEmailForm
from .models import CustomerType
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic import View, TemplateView, DeleteView, ListView, DetailView
from django.db import transaction
from django.contrib import messages
from .models import Customer
from django.db.models.functions import Concat
from django.db.models import Value, F

# Create your views here.
class CoustomerView(LoginRequiredMixin, View):
    template_name = 'Customers_Sales/customer_form.html'
    success_url = 'Customer_Sales:home'

    def get(self, request, *args, **kwargs):
        ctx = {
            'forms':{
                'customer_form' : CustomerForm(),
                'customer_address_form' : CustomerAddressForm(),
                'cutomer_note_form': CustomerNoteForm(),
                'customer_email_form': CustomerEmailForm()
            }
        }

        ctx['forms']['customer_form'].fields["customer_type"].queryset = CustomerType.objects.filter(owner=request.user)

        return render(request, self.template_name, ctx)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ctx = {
            'forms':{
                'customer_form' : CustomerForm(request.POST),
                'customer_address_form' : CustomerAddressForm(request.POST),
                'cutomer_note_form': CustomerNoteForm(request.POST),
                'customer_email_form': CustomerEmailForm(request.POST)
            }
        }

        forms_vaild = True
        for key in ctx['forms'].keys():
            if ctx['forms'][key].is_valid() == False:
                forms_vaild = False
                return render(request, self.template_name, ctx)

        if forms_vaild:
            customer = ctx['forms']['customer_form'].save(commit=False)
            owner = self.request.user
            customer.owner = owner
            customer.save()
            address = ctx['forms']['customer_address_form'].save(commit=False)
            address.customer = customer
            address.save()
            note = ctx['forms']['cutomer_note_form'].save(commit=False)
            note.customer = customer
            note.save()
            email = ctx['forms']['customer_email_form'].save(commit=False)
            email.customer = customer
            email.save()
            messages.success(request, 'Your Customer Was Created successfully')

        return redirect(reverse_lazy(self.success_url))


        




class Home(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/customers_sales_index.html'


class CustomerListView(LoginRequiredMixin, ListView):
    template_name = 'Customers_Sales/customer_list.html'
    model = Customer
    paginate_by = 20
    ordering  = ['-id']

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset().filter(
                owner=self.request.user
            ).annotate(
                customer_full_name = Concat(F('first_name'), Value(' '), F('middle_name'), Value(' '), F('last_name'))

            ).values(
                'id',
                'customer_full_name'
            )
        return qs



class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "Customers_Sales/customer_delete.html"
    model = Customer

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset().filter(
                owner=self.request.user
            )
        return qs