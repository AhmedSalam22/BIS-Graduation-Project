from django.forms import ModelForm
from .models import Journal  , Accounts
from django import forms
import django_filters


class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

class AccountForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account']
    
    
    def __init__(self, user=None ,    **kwargs ):
        super().__init__(**kwargs)
        self.fields["account"].queryset = Accounts.objects.filter(owner=user)



class JournalFilter( django_filters.FilterSet):
    class Meta:
        model = Journal
        fields = ['account', 'date' , 'balance' , "transaction_type"]

    def __init__(self,   **kwargs):
        super().__init__(**kwargs)
        self.form.fields["account"].queryset = Accounts.objects.filter(owner=self.request.user)