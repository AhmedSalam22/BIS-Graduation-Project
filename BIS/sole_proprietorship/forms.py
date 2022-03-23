from django.forms import ModelForm
from .models import Journal  , Accounts , ReportingPeriodConfig, Transaction
from django import forms
import django_filters
from django.utils import timezone
from django.forms import formset_factory 
from django.forms import BaseFormSet
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout , Row , Column , Submit , Div
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory, BaseInlineFormSet
from .from_mixin import TransactionValidation

class JournalFormSetForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account', 'balance' , "transaction_type"]
        # widgets = {
        #     "comment":forms.Textarea(attrs={"placeholder":"Type Comment about specific transaction" , "rows":"2"})
        # }

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)

        self.user = user
        self.fields['account'].queryset = Accounts.objects.filter(owner = user)
        self.fields['account'].widget.attrs.update({'class': 'select2'})
        # self.fields['date'].widget =  forms.widgets.DateInput(attrs={'type': 'date'})
        # self.fields["date"].initial = timezone.localdate()
          
class BaseJournalFormSet(TransactionValidation, BaseFormSet):
    pass

JournalFormSet = formset_factory(JournalFormSetForm ,
                                     formset= BaseJournalFormSet,
                                     min_num = 2,
                                     extra= 0,
                                     validate_min= True )
                                     
class JournalFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
           Div(
                Row(Column('account'), Column('balance') , Column('transaction_type')), 
                css_class='link-formset')
           
        )
        self.render_required_fields = True
        self.form_tag = False
        # self.template = 'bootstrap/table_inline_formset.html'



class JournalForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account', 'balance' , "transaction_type"]


class AccountForm(ModelForm):
    class Meta:
        model = Journal
        fields = ['account']
    
    
    def __init__(self, user=None ,    **kwargs ):
        super().__init__(**kwargs)
        self.fields["account"].queryset = Accounts.objects.filter(owner=user)



# class JournalFilter( django_filters.FilterSet):
#     class Meta:
#         model = Journal
#         fields = ['account', 'date' , 'balance' , "transaction_type"]

#     def __init__(self,   **kwargs):
#         super().__init__(**kwargs)
#         self.form.fields["account"].queryset = Accounts.objects.filter(owner=self.request.user)



class UploadFileForm(forms.Form):
    file = forms.FileField()


class ReportingPeriodConfigForm(forms.ModelForm):
    class Meta:
        model = ReportingPeriodConfig
        fields = ['company_name', 'start_date' , 'end_date']
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

        if Accounts.objects.filter(owner=user, account__iexact=account).exists():
            raise forms.ValidationError(_("this account is already exist"),
                        code="duplicate",
                        params={"value": account}
        )



class TransactionForm(ModelForm):
    class Meta:
        model = Transaction
        fields = ['date', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows':2}),
            'date': forms.widgets.DateInput(attrs={'type': 'date'}),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now()
        

class TransactionFilter(django_filters.FilterSet):
    balance__gte = django_filters.NumberFilter(field_name='journal__balance', label='balance is >=', lookup_expr='gte') 
    balance__lte = django_filters.NumberFilter(field_name='journal__balance', label='balance is <=', lookup_expr='lte') 

    class Meta:
        model = Transaction
        fields = {
                'date': ['gte', 'lte'],
                'comment': ['icontains'],
                }


    # @property
    # def qs(self):
    #     parent = super().qs
    #     return parent.prefetch_related(
    #         'journal_set' , 'journal_set__account'
    #     ).filter(journal__account__owner=self.request.user).distinct()


    def __init__(self, *args,   **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields["date__gte"].widget =forms.widgets.DateInput(attrs={'type': 'date'})
        self.form.fields["date__gte"].label = 'Start Date'
        self.form.fields["date__lte"].widget =forms.widgets.DateInput(attrs={'type': 'date'})
        self.form.fields["date__lte"].label = 'End Date'
        self.form.fields['comment__icontains'].widget = forms.Textarea(attrs={'rows':2, 'cols':30})


        
class TransactionFilterHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
           Div(
                Row('date__gte',
                    'date__lte' ,
                    'balance__gte',
                     'balance__lte',
                    'comment__icontains'
                ) 
            ),
        )
        
        self.form_tag = False

class CustomTransactionFormSet(TransactionValidation, BaseInlineFormSet):
    pass


     

TransactionFormSet = inlineformset_factory(
    Transaction, Journal, fields=('account', 'balance' , "transaction_type"),
    formset= CustomTransactionFormSet, extra = 3
    )

                                     
class TransactionFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
           Div(
                Row(Column('account'), Column('balance') , Column('transaction_type', 'DELETE')),
           )
        )
        self.render_required_fields = True
        self.form_tag = False
     



class LedgerFilterForm(forms.Form):
    account =  forms.ModelChoiceField(queryset= Accounts.objects.none(), required=True)
    start_date = forms.DateField(required=True,  widget= forms.widgets.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required= True, widget= forms.widgets.DateInput(attrs={'type': 'date'}))


    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super().__init__(*args, **kwargs)
        self.fields['account'].queryset  = Accounts.objects.filter(owner=self.request.user)
        self.fields['start_date'].initial = self.request.user.fs_reporting_period.start_date
        self.fields['end_date'].initial = self.request.user.fs_reporting_period.end_date