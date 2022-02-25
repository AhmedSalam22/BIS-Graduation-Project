from django.shortcuts import render
from django.views.generic import View, TemplateView, DeleteView, ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.functions import Concat
from django.db.models import Value, F
from .models import Supplier
from django.contrib import messages

# Create your views here.
class CreateSupplierView(LoginRequiredMixin, CreateView):
    template_name = 'suppliers/create_supplier.html'
    model = Supplier
    fields = ['first_name', 'middle_name', 'last_name']

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        messages.success(self.request, 'Your supplier has been created.')
        return super().form_valid(form)


class SupplierListView(LoginRequiredMixin, ListView):
    template_name = 'suppliers/supplier_list.html'
    model = Supplier
    paginate_by = 20
    ordering  = ['-id']

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




class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "suppliers/create_supplier.html"
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