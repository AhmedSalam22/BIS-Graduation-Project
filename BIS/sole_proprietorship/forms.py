from django.forms import ModelForm
from .models import Journal  , Accounts
from django import forms
import django_filters

def create_form(user):
    """Returns a new model form which uses the correct queryset for user
    https://stackoverflow.com/questions/20276302/passing-arguments-to-modelform-through-formset
    
    """

    class JournalFormUser(forms.ModelForm):

        class Meta:
            model = Journal
            fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]


        def __init__(self, *args, **kwargs):
            super(JournalFormUser, self).__init__(*args, **kwargs)
            self.fields['account'].queryset = Accounts.objects.filter(owner = user)
            self.fields['account'].widget.attrs.update({'class': 'select2'})
            self.fields['date'].widget =  forms.widgets.DateInput(attrs={'type': 'date'})


    return JournalFormUser

class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

    # def __init__(self,    **kwargs ):
    #     # experiment = kwargs.pop('experiment')
    #     super().__init__(**kwargs)
    #     self.fields["account"].queryset = Accounts.objects.filter(owner=1)

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



class UploadFileForm(forms.Form):
    file = forms.FileField()
