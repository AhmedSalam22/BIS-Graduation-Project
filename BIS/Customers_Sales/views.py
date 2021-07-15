from django.shortcuts import render , reverse
from .forms import CustomerForm , CustomerAddressForm , CustomerNoteForm , TelephoneForm , CustomerEmailForm
from .models import CustomerType
from home.multi_form_view import MyMultiFormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
# Create your views here.


class CoustomerView(LoginRequiredMixin , MyMultiFormView):
    template_name = 'Customers_Sales/customer_form.html'

    form_classes = {
        'customer_form' : CustomerForm,
        'customer_address_form' : CustomerAddressForm,
        'cutomer_note_form': CustomerNoteForm,
        'customer_telepone_form':TelephoneForm ,
        'customer_email_form': CustomerEmailForm
    }

    def get_forms(self, request):
        forms = super(CoustomerView , self).get_forms(request)
        forms['customer_form'].fields["customer_type"].queryset = CustomerType.objects.filter(owner=request.user)
        return forms


    def forms_valid(self, forms):
        customer = forms['customer_form'].save(commit=False)
        owner = self.request.user
        customer.owner = owner
        customer.save()
        address = forms['customer_address_form'].save(commit=False)
        address.customer = customer
        address.save()
        note = forms['cutomer_note_form'].save(commit=False)
        note.customer = customer
        note.save()
        email = forms['customer_email_form'].save(commit=False)
        email.customer = customer
        email.save()
        phone = forms['customer_telepone_form'].save(commit=False)
        phone.customer = customer
        phone.save()



        return super(CoustomerView, self).forms_valid(forms)

    def get_success_url(self):
        return reverse('home:home')



class Home(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/customers_sales_index.html'
