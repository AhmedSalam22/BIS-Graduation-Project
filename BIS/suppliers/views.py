from django.shortcuts import render
from django.views.generic import View, TemplateView, DeleteView, ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Supplier

# Create your views here.
class CreateSupplierView(LoginRequiredMixin, CreateView):
    template_name = 'suppliers/create_supplier.html'
    model = Supplier
    fields = ['first_name', 'middle_name', 'last_name']

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        return super().form_valid(form)


class SupplierListView(LoginRequiredMixin, ListView):
    pass

