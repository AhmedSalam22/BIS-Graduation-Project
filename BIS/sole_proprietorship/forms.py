from django.forms import ModelForm
from .models import Journal  , Accounts , ReportingPeriodConfig
from django import forms
import django_filters
from django.utils import timezone
from django.forms import modelformset_factory 
from django.forms import BaseFormSet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout , Row , Column
from django.utils.translation import gettext as _



class JournalFormSetForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]
        widgets = {
            "comment":forms.Textarea(attrs={"placeholder":"Type Comment about specific transaction" , "rows":"2"})
        }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.fields['account'].queryset = Accounts.objects.filter(owner = user)
        self.fields['account'].widget.attrs.update({'class': 'select2'})
        self.fields['date'].widget =  forms.widgets.DateInput(attrs={'type': 'date'})
        self.fields["date"].initial = timezone.localdate()
      


JournalFormSet = modelformset_factory(Journal ,
                                     fields=['account', 'date' , 'balance' , "transaction_type" , "comment"] ,
                                     form=JournalFormSetForm,
                                     min_num=2 , 
                                     extra= 0,
                                     validate_min= True )

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


class ReportingPeriodConfigForm(forms.ModelForm):
    class Meta:
        model = ReportingPeriodConfig
        fields = ['start_date' , 'end_date']
        widgets = {
                'start_date': forms.widgets.DateInput(attrs={'type': 'date'}),
                'end_date': forms.widgets.DateInput(attrs={'type': 'date'}),
            }

class AccountsForm(ModelForm):
    class Meta:
        model = Accounts
        fields = '__all__'
        exclude = ["owner"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user


    def clean(self , *args, **kwargs):
        user = self.user
        account = self.cleaned_data.get("account")

        if Accounts.objects.filter(owner__username__iexact=user, account__iexact=account).exists():
            raise forms.ValidationError(_("this account is already exist"),
                        code="duplicate",
                        params={"value": account}
        )



    