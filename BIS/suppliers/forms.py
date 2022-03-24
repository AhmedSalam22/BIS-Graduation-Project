from django import forms
from suppliers.models import Supplier, SupplierEmail, SupplierPhone, SupplierAddress, SupplierNote

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier 
        exclude = ('owner', 'name')

class SupplierEmailForm(forms.ModelForm):
    class Meta:
        model = SupplierEmail
        exclude = ('supplier',)


class SupplierPhoneForm(forms.ModelForm):
    class Meta:
        model = SupplierPhone
        exclude = ('supplier',)


class SupplierAddressForm(forms.ModelForm):
    class Meta:
        model = SupplierAddress
        exclude = ('supplier',)


class SupplierNoteForm(forms.ModelForm):
    class Meta:
        model = SupplierNote
        exclude = ('supplier',)