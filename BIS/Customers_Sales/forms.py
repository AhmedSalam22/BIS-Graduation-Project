from django import forms
from .models import (
    Customer, 
    CustomerAddress, 
    CustomerEmail, 
    CustomerNote,
    CustomerPhone
)

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['first_name',
          'middle_name' , 
          'last_name' , 
        ] 
   
        

class CustomerAddressForm(forms.ModelForm):
    class Meta:
       model = CustomerAddress
       fields = ['address1',
                 'address2',
                 'zip_code',
                 'city',
                 'country'
       ]
     

class CustomerNoteForm(forms.ModelForm):
    class Meta:
        model = CustomerNote
        fields = ['note']


class CustomerEmailForm(forms.ModelForm):
    class Meta:
        model = CustomerEmail
        fields = ['email']


class CustomerPhoneForm(forms.ModelForm):
    class Meta:
        model = CustomerPhone
        fields = ['phone']