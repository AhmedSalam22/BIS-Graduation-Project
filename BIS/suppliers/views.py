from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.views.generic import View, TemplateView, DeleteView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Concat
from django.db.models import Value, F
from .models import Supplier, SupplierPhone, SupplierNote, SupplierAddress, SupplierEmail
from django.contrib import messages
from suppliers.forms import SupplierForm, SupplierEmailForm, SupplierPhoneForm, SupplierAddressForm, SupplierNoteForm
from django_filters.views import FilterView
from suppliers.filters import SupplierFilter
# Create your views here.
class CreateSupplierView(LoginRequiredMixin, View):
    template_name = 'suppliers/create_supplier.html'
    success_url = None

    def get(self, request, *args, **kwargs):
        ctx = {}
        ctx['supplier_form'] = SupplierForm()
        ctx['supplier_email_form'] = SupplierEmailForm()
        ctx['supplier_phone_form'] = SupplierPhoneForm()
        ctx['supplier_address_form'] = SupplierAddressForm()
        ctx['supplier_note_form'] = SupplierNoteForm()
        return render(request, self.template_name, ctx)

    def post(self, request):
        supplier_form = SupplierForm(request.POST)
        supplier_email_form = SupplierEmailForm(request.POST)
        supplier_phone_form = SupplierPhoneForm(request.POST)
        supplier_address_form = SupplierAddressForm(request.POST)
        supplier_note_form = SupplierNoteForm(request.POST)

        ctx = {
            'supplier_form': supplier_form,
            'supplier_email_form': supplier_email_form,
            'supplier_phone_form': supplier_phone_form,
            'supplier_address_form': supplier_address_form,
            'supplier_note_form': supplier_note_form
        }

        if supplier_form.is_valid() and supplier_email_form.is_valid() and supplier_phone_form.is_valid() \
            and supplier_address_form.is_valid() and supplier_note_form.is_valid():
            supplier = supplier_form.save(commit=False)
            supplier.owner = request.user
            supplier.save()

            if supplier_email_form.cleaned_data['email']:
                supplier_email = supplier_email_form.save(commit=False)
                supplier_email.supplier = supplier
                supplier_email.save()
           
            if supplier_phone_form.cleaned_data['phone']:
                supplier_phone = supplier_phone_form.save(commit=False)
                supplier_phone.supplier = supplier
                supplier_phone.save()

            if any(supplier_address_form.cleaned_data.values()):
                supplier_address = supplier_address_form.save(commit=False)
                supplier_address.supplier = supplier
                supplier_address.save()

            if supplier_note_form.cleaned_data['note']:
                supplier_note = supplier_note_form.save(commit=False)
                supplier_note.supplier = supplier
                supplier_note.save()

            return redirect(self.success_url)
        return render(request, self.template_name, ctx)


# class CreateSupplierView(LoginRequiredMixin, CreateView):
#     template_name = 'suppliers/create_supplier.html'
#     model = Supplier
#     fields = ['first_name', 'middle_name', 'last_name']

#     def form_valid(self, form):
#         self.object = form.save(commit=False)
#         self.object.owner = self.request.user
#         self.object.save()
#         messages.success(self.request, 'Your supplier has been created.')
#         return super().form_valid(form)


class SupplierListView(LoginRequiredMixin, FilterView):
    template_name = 'suppliers/supplier_list.html'
    model = Supplier
    paginate_by = 20
    ordering  = ['-id']
    filterset_class = SupplierFilter

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset().filter(
                owner=self.request.user
            ).annotate(
                full_name = Concat(F('first_name'), Value(' '), F('middle_name'), Value(' '), F('last_name'))

            ).values(
                'id',
                'full_name'
            )
        return qs



class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    template_name = "suppliers/supplier_delete.html"
    model = Supplier

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset().filter(
                owner=self.request.user
            )
        return qs


class SupplierDetailView(LoginRequiredMixin, DetailView):
    template_name = "suppliers/supplier_detail.html"
    model = Supplier

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset().filter(
                owner=self.request.user
            ).prefetch_related(
                'suppliernote_set',
                'supplieremail_set',
                'supplierphone_set',
                'supplieraddress_set'
            )
        return qs




class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "suppliers/update_supplier.html"
    model = Supplier
    fields = ('first_name', 'middle_name', 'last_name')

    def get_queryset(self):
        """ Limit a User to only modifying their own data. """
        qs = super(SupplierUpdateView, self).get_queryset()
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        messages.success(self.request, 'Supplier has been updated.')
        return super().form_valid(form)


class AddFieldToSupplierMixin:
    Form = None
    form_ctx_name = 'form'
    success_url = 'suppliers:supplier_detail'
    template_name = 'suppliers/add_to_supplier.html'
    title = None

    def get(self, request, *args, **kwargs):
        supplier = get_object_or_404(Supplier, pk=kwargs['supplier_id'], owner=request.user)
        ctx = {
            self.form_ctx_name: self.Form(),
            'title': self.title
        }
        return render(request, self.template_name, ctx)


    def post(self, request, *args, **kwargs):
        supplier = get_object_or_404(Supplier, pk=kwargs['supplier_id'], owner=request.user)
        form = self.Form(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.supplier = supplier
            obj.save()
            return redirect(reverse(self.success_url, args=[supplier.pk]))
        return render(request, self.tamplate_name, {self.form_ctx_name: form, 'title': self.title})

class AddPhoneView(LoginRequiredMixin, AddFieldToSupplierMixin,  View):
    Form = SupplierPhoneForm
    title = 'Phone'
   

class AddEmailView(LoginRequiredMixin, AddFieldToSupplierMixin,  View):
    Form = SupplierEmailForm
    title = 'Email'

class AddNoteView(LoginRequiredMixin, AddFieldToSupplierMixin,  View):
    Form = SupplierNoteForm
    title = 'Note'

class AddAddressView(LoginRequiredMixin, AddFieldToSupplierMixin,  View):
    Form = SupplierAddressForm
    title = 'Address'

class UpdateDeleteMixin:
    """
        Mixin for Supplier Phone,Email, Address , and Note
    """
    success_url = 'suppliers:supplier_detail'

    def get_success_url(self):
        return reverse(self.success_url, args=[self.kwargs['supplier_pk']])

    def get_queryset(self):
        """ Limit a User to only modifying their own data. """
        qs = super().get_queryset().filter(supplier__owner=self.request.user)
        return qs


class SupplierPhoneUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "suppliers/update_supplier.html"
    model = SupplierPhone
    fields = ['phone',]

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        messages.success(self.request, 'Supplier Phone has been updated.')
        return super().form_valid(form)

class SupplierAddressUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "suppliers/update_supplier_address.html"
    model = SupplierAddress
    fields = ['address1', 'address2', 'zip_code', 'city', 'country']

class SupplierNoteUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "suppliers/update_supplier_note.html"
    model = SupplierNote
    fields = ['note',]

class SupplierEmailUpdateView(LoginRequiredMixin, UpdateDeleteMixin,  UpdateView):
    template_name = "suppliers/update_supplier_email.html"
    model = SupplierEmail
    fields = ['email',]


class SupplierPhoneDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "suppliers/supplier_phone_delete.html"
    model = SupplierPhone


class SupplierEmailDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "suppliers/supplier_email_delete.html"
    model = SupplierEmail


class SupplierAddressDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "suppliers/supplier_address_delete.html"
    model = SupplierAddress


class SupplierNoteDeleteView(LoginRequiredMixin, UpdateDeleteMixin, DeleteView):
    template_name = "suppliers/supplier_note_delete.html"
    model = SupplierNote


    