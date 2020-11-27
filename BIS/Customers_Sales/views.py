from django.shortcuts import render , reverse
from multi_form_view import MultiFormView
from .forms import CustomerForm , CustomerAddressForm , CustomerNoteForm

# Create your views here.


class CoustomerView(MultiFormView):
    form_classes = {
        'customer_form' : CustomerForm,
        'customer_address_form' : CustomerAddressForm,
        'cutomer_note_form': CustomerNoteForm,
    }
    template_name = 'Customers_Sales/test.html'

    def forms_valid(self, forms):
        customer = forms['customer_form'].save(commit=False)
        owner = self.request.user
        customer.owner = owner
        customer.save()
        address = forms['customer_address_form'].save(commit=False)
        address.owner = owner
        address.customer = customer
        address.save()
        note = forms['cutomer_note_form'].save(commit=False)
        note.owner = owner
        note.customer = customer
        note.save()

        return super(CoustomerView, self).forms_valid(forms)

    def get_success_url(self):
        return reverse('home:home')