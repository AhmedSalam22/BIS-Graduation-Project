from django.shortcuts import render , reverse, redirect, get_object_or_404
from django.urls import  reverse_lazy
from .forms import (
    CustomerForm, 
    CustomerAddressForm, 
    CustomerNoteForm, 
    CustomerEmailForm,
    CustomerPhoneForm
)
from .models import (
    Customer,
    CustomerAddress,
    CustomerEmail,
    CustomerNote,
    CustomerPhone
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic import View, TemplateView, DeleteView, ListView, DetailView, UpdateView
from django.db import transaction
from django.contrib import messages
from .models import Customer
from django.db.models.functions import Concat
from django.db.models import Value, F
from django_filters.views import FilterView
from .filters import CustomerFilter
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
            if any(ctx['forms']['customer_address_form'].cleaned_data.values()):
                address = ctx['forms']['customer_address_form'].save(commit=False)
                address.customer = customer
                address.save()
            if ctx['forms']['cutomer_note_form'].cleaned_data['note']:
                note = ctx['forms']['cutomer_note_form'].save(commit=False)
                note.customer = customer
                note.save()
            if ctx['forms']['customer_email_form'].cleaned_data['email']:
                email = ctx['forms']['customer_email_form'].save(commit=False)
                email.customer = customer
                email.save()
            messages.success(request, 'Your Customer Was Created successfully')

        return redirect(reverse_lazy(self.success_url))


        




class Home(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/customers_sales_index.html'


class CustomerListView(LoginRequiredMixin, FilterView):
    template_name = 'Customers_Sales/customer_list.html'
    model = Customer
    paginate_by = 20
    ordering  = ['-id']
    filterset_class = CustomerFilter

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



class CustomerDetailView(LoginRequiredMixin, DetailView):
    template_name = "Customers_Sales/customer_detail.html"
    model = Customer

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset().filter(
                owner=self.request.user
            ).prefetch_related(
                'customernote_set',
                'customeremail_set',
                'customerphone_set',
                'customeraddress_set'
            )
        return qs




class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "Customers_Sales/update_customer.html"
    model = Customer
    fields = ('first_name', 'middle_name', 'last_name')

    def get_queryset(self):
        """ Limit a User to only modifying their own data. """
        qs = super(CustomerUpdateView, self).get_queryset()
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        messages.success(self.request, 'Customer has been updated.')
        return super().form_valid(form)


class AddFieldToCustomerMixin:
    Form = None
    form_ctx_name = 'form'
    success_url = 'Customer_Sales:customer_detail'
    template_name = "Customers_Sales/add_to_customer.html"
    title = None

    def get(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=kwargs['customer_id'], owner=request.user)
        ctx = {
            self.form_ctx_name: self.Form(),
            'title': self.title
        }
        return render(request, self.template_name, ctx)


    def post(self, request, *args, **kwargs):
        customer = get_object_or_404(Customer, pk=kwargs['customer_id'], owner=request.user)
        form = self.Form(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.customer = customer
            obj.save()
            return redirect(reverse(self.success_url, args=[customer.pk]))
        return render(request, self.tamplate_name, {self.form_ctx_name: form, 'title': self.title})

class AddPhoneView(LoginRequiredMixin, AddFieldToCustomerMixin,  View):
    Form = CustomerPhoneForm
    title = 'Phone'
   

class AddEmailView(LoginRequiredMixin, AddFieldToCustomerMixin,  View):
    Form = CustomerEmailForm
    title = 'Email'

class AddNoteView(LoginRequiredMixin, AddFieldToCustomerMixin,  View):
    Form = CustomerNoteForm
    title = 'Note'

class AddAddressView(LoginRequiredMixin, AddFieldToCustomerMixin,  View):
    Form = CustomerAddressForm
    title = 'Address'

class UpdateDeleteMixin:
    """
        Mixin for Customer Phone,Email, Address , and Note
    """
    success_url = 'Customer_Sales:customer_detail'

    def get_success_url(self):
        return reverse(self.success_url, args=[self.kwargs['customer_pk']])

    def get_queryset(self):
        """ Limit a User to only modifying their own data. """
        qs = super().get_queryset().filter(customer__owner=self.request.user)
        return qs


class CustomerPhoneUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "Customers_Sales/update_customer.html"
    model = CustomerPhone
    fields = ['phone',]

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        messages.success(self.request, 'Customer Phone has been updated.')
        return super().form_valid(form)

class CustomerAddressUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "Customers_Sales/update_customer_address.html"
    model = CustomerAddress
    fields = ['address1', 'address2', 'zip_code', 'city', 'country']

class CustomerNoteUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "Customers_Sales/update_customer_note.html"
    model = CustomerNote
    fields = ['note',]

class CustomerEmailUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "Customers_Sales/update_customer_email.html"
    model = CustomerEmail
    fields = ['email',]


class CustomerPhoneDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "Customers_Sales/customer_phone_delete.html"
    model = CustomerPhone


class CustomerEmailDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "Customers_Sales/customer_email_delete.html"
    model = CustomerEmail


class CustomerAddressDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "Customers_Sales/customer_address_delete.html"
    model = CustomerAddress


class CustomerNoteDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "Customers_Sales/customer_note_delete.html"
    model = CustomerNote