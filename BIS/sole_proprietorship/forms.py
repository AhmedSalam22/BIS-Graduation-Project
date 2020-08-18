from django.forms import ModelForm
from .models import Journal  , Accounts
from django import forms

class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

class AccountForm(forms.Form):
    account_name = forms.CharField()

