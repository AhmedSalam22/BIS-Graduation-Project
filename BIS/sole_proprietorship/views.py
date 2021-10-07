from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import HttpResponse , HttpResponseRedirect, JsonResponse, StreamingHttpResponse
from django.urls import reverse
from django.shortcuts import render , redirect
from .models import Journal , Accounts, Transaction
from .owner import OwnerListView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import ( JournalForm, AccountForm,TransactionFilterHelper,
                    UploadFileForm, ReportingPeriodConfigForm,
                    JournalFormSet, AccountsForm, TransactionForm, TransactionFilter,
                    TransactionFormSet, TransactionFormSetHelper, LedgerFilterForm
                    )

import pandas as pd
import numpy as np
import csv
from django.utils import timezone
from django.db.models import Avg
import plotly.graph_objects as go
import plotly
import plotly.express as px
from django_filters.views import FilterView
from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
import xlsxwriter
# from pivottablejs import pivot_ui
from django.contrib import messages
from django.db.models import Q
from .forms import JournalFormSetHelper
from django.shortcuts import get_object_or_404
from django.views.generic import DeleteView
from django.db import transaction
from django.utils.safestring import mark_safe
import plotly.figure_factory as ff
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView
import functools

# from django_renderpdf.views import PDFView

def prepare_data_frame( journal  ,  accounts):
    accounts = pd.DataFrame(accounts)
    journal  = pd.DataFrame(journal)
    # prepare Data Frame
    accounts.drop(columns="owner_id" , inplace=True)
    journal.drop(columns="owner_id" , inplace=True)
    data = accounts.merge(journal , left_on="id" , right_on = "account_id" , how="outer")
    # return True or false if transaction_type == Normal Balance
    data["helper1"] = data["normal_balance"] == data["transaction_type"]
    #convert True, False to 1,-1 respectively
    data["helper1"] = data["helper1"].replace([True, False] , [1,-1])
    #convert balance into negative in case the transaction
    data["balance_negative"] = data["helper1"] * data["balance"]

    return data


def prepare_trial_balance(df):
    trial_balance = df.pivot_table(values="balance_negative" , index="account" , columns="normal_balance" ,aggfunc=np.sum, fill_value=0)
    return trial_balance , trial_balance.sum()


def prepare_net_income(df):
    net_income = df.query('account_type == "Revenue" or account_type == "Expenses" ').pivot_table(index = "account" , columns="account_type" , values="balance_negative" , aggfunc=np.sum).sort_values('Revenue' , ascending=False)
    return net_income , net_income.sum()

def prepare_equity_statement(df):
    investment = df.query('account_type == "Investment"')["balance_negative"].sum()
    drawings = df.query('account_type == "Drawings"')["balance_negative"].sum()
    return  investment , drawings 

def prepare_finacial_statement(df):
    assest = df.query('account_type == "Assest"').pivot_table(values="balance_negative" , index="account" , columns="normal_balance" ,aggfunc=np.sum, fill_value=0)
    total_assest= assest.sum()
    assest[""] = ""
    
    liabilities = df.query('account_type == "liabilities"').pivot_table(values="balance_negative" , index="account" , columns="normal_balance" ,aggfunc=np.sum, fill_value=0)
    total_liabilities = liabilities.sum()
    return assest , total_assest , liabilities ,total_liabilities


class ConfigRequiredMixin:
     def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'fs_reporting_period'):
            messages.info(request , "“It looks like it’s your first time. Please complete the Report setting first before continuing")
            return redirect(reverse("sole_proprietorship:ReportingPeriodConfig"))
        return super().dispatch(request, *args, **kwargs)



class AccountsListView(LoginRequiredMixin, ListView):
    # paginate_by = 10
    model = Accounts

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user).values('account', 'normal_balance', 'account_type', 'id', 'classification')


class AccountsCreateView(LoginRequiredMixin, CreateView):
    template_name = 'sole_proprietorship/accounts_form.html'
    form_class = AccountsForm
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user # pass the 'user' in kwargs
        return kwargs 

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        messages.success(self.request, 'Your account has been created.')

        return super().form_valid(form)


class AccountsUpdateView(OwnerUpdateView):
    model = Accounts
    fields = ('account', 'normal_balance', 'account_type', 'classification')

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save()
        messages.success(self.request, 'Account has been updated.')
        return super().form_valid(form)

class AccountsDeleteView(OwnerDeleteView):
    model = Accounts


class TransactionListView(LoginRequiredMixin, FilterView):
    paginate_by = 10
    model = Transaction
    ordering = ["-date"]
    template_name = "sole_proprietorship/transaction_list.html"
    filterset_class = TransactionFilter
    helper = TransactionFilterHelper()


    def get_queryset(self):
        qs = super().get_queryset().prefetch_related(
            'journal_set' , 'journal_set__account'
        ).filter(journal__account__owner=self.request.user).distinct()
        return qs


    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        query = Transaction.my_objects.total_debit_and_total_credit(self.request.user.id,
         end_date= self.request.GET.get('date__lte', None))
        ctx['Debit'], ctx['Credit'] = query.get('Debit') , query.get('Credit')
        ctx['helper'] = self.helper
        return ctx


    def get(self, request, *args, **kwargs):
        request.session['export_journal'] = request.GET
        return super().get(request, *args, **kwargs)



class Echo:
    """An object that implements just the write method of the file-like
    interface.
    ref: https://docs.djangoproject.com/en/3.2/howto/outputting-csv/
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class ExportTrsanctionView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        f = TransactionFilter(request.session.get('export_journal'))
        queryset = f.qs.prefetch_related(
            'journal_set' , 'journal_set__account'
        ).filter(journal__account__owner=request.user).distinct()


        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        writer.writerow(['Date', 'Account', 'balance', 'transaction type' , 'comment'])

        response = StreamingHttpResponse(
            streaming_content=(writer.writerow(
                    [transaction.date , journal.account , journal.balance , journal.transaction_type , transaction.comment ]
                )  for transaction in queryset for journal in transaction.journal_set.all() 
            ),
        content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="journal.csv"'
        return response



class JournalCreateView(LoginRequiredMixin , View):
    template_name = 'sole_proprietorship/journal_form.html'
    success_url = None

    def __init__(self, *args, **kwargs):
        self.ctx = self.populate_ctx()
        super().__init__(*args, **kwargs)

    def populate_ctx(self):
        helper = JournalFormSetHelper()
        return {'helper': helper}

    def get(self , request , *args, **kwargs):
        JournalFormSetForm = JournalFormSet(form_kwargs={'user': request.user} )
        self.ctx['formset'] = JournalFormSetForm
        self.ctx['transaction_form'] = TransactionForm()
        return render(request, self.template_name , self.ctx )

    @transaction.atomic
    def post(self , request , *args , **kwargs):

        self.ctx['formset'] = JournalFormSet(request.POST , form_kwargs={'user': request.user})
        self.ctx['transaction_form'] = TransactionForm(request.POST)

        # do whatever you'd like to do with the valid formset
        if self.ctx['formset'].is_valid() and self.ctx['transaction_form'].is_valid():
            transaction = self.ctx['transaction_form'].save(commit=False)
            transaction.save()

            for journal_form in self.ctx['formset']:
                journal = journal_form.save(commit=False)
                journal.transaction = transaction
                journal.save()
            messages.success(request, 'Your Transaction Was Created Succesffuly')
            return redirect(self.success_url)
        return render(request, self.template_name , self.ctx)



class JournalUpdateView(OwnerUpdateView):
    model = Journal
    fields = ['account', 'balance' , "transaction_type"]

class JournalDeleteView(OwnerDeleteView):
    model = Journal

    def get_queryset(self):
        qs = super(OwnerDeleteView, self).get_queryset()
        return qs.filter(account__owner=self.request.user)

class FinancialStatements(LoginRequiredMixin, ConfigRequiredMixin, View):
    template_name  = "sole_proprietorship/financial_statements.html"
    def financial_sataements_by_pandas(self):
        owner=self.request.user
        # Accounts.objects.filter(owner=owner)[0].journal_set.values()
        #Accounts.objects.filter(owner=owner).all().values()

        accounts = Accounts.objects.filter(owner=owner).all().values()
        journal = Journal.objects.filter(account__owner=owner).distinct().all().values()
        data = prepare_data_frame(journal , accounts)
        trial_balance = prepare_trial_balance(data)
        net_income =  prepare_net_income(data)
        try:
            amount = net_income[1][1] - net_income[1][0]
        except:
            amount = 0
        investment ,  drawings = prepare_equity_statement(data)
        equity = investment + amount - drawings

        assest , total_assest , liabilities ,total_liabilities = prepare_finacial_statement(data)

        ctx = {
            "trial_balance": trial_balance[0].to_html(classes = "table table-hover table-borderless") , 
            "debit_credit" : trial_balance[1] , 
            "net_income" : net_income[0].to_html(classes = "table table-hover table-borderless") ,
            "revenue_expenses": net_income[1] , 
            "amount"  : amount , 
            "investment" : investment , 
            "drawings" : drawings ,
            "equity": equity ,
            "assest": assest.to_html(classes = "table table-hover table-borderless"), 
            "total_assest" : total_assest[0] ,
            "liabilities" : liabilities.to_html(classes = "table table-hover table-borderless") ,
            "total_liabilities" : total_liabilities[0]
        }
        return ctx

        
    def get_data(self):
        with connection.cursor() as cursor:
            cursor.execute(""" 
            SELECT   account_type , account  , normal_balance , sum(helper) as balance FROM (
                                                    SELECT * ,
                                                    CASE
                                                        WHEN j.transaction_type = a.normal_balance Then  j.balance
                                                        ELSE ( -1 * j.balance)
                                                    END as helper 
                                                    FROM sole_proprietorship_journal as j
                                                    JOIN sole_proprietorship_accounts as a
                                                    on j.account_id = a.id
                                                    JOIN sole_proprietorship_transaction as t
                                                    ON j.transaction_id = t.id
                                                    where a.owner_id = %s  AND t.date <= %s
                                    ) as temp_table
    GROUP by account_type , account, normal_balance
    ORDER by balance DESC
                                                    """ , [self.request.user.id ,
                                                           self.request.user.fs_reporting_period.end_date
                                                           
                                                            ])

            # query result will be some thing like this ('Assest', 'Computer equipment','Debit', 7000.0)
            query = list(cursor)
        return query

    def financial_sataements_by_sql(self):
        query = self.get_data()
        total_debit = sum([ var[3] for var in query if var[2] == "Debit"])
        total_credit = sum([ var[3] for var in query if var[2] == "Credit"])

        ctx = {
            'data': query ,
            'Total_Debit' :total_debit ,
            'Total_Credit' : total_credit 
        }
        # dic acumulation to get the blance for oue expanded account equation (Assest = Liabilities + revenues - Expenses + investment - Drawings )
        for var in query:
            ctx[var[0]] = ctx.get(var[0] , 0) + var[3]

        ctx["net_income"] = ctx.get('Revenue' , 0) - ctx.get('Expenses' , 0)
        ctx['equity'] = ctx.get('Investment' , 0)  + ctx["net_income"] - ctx.get('Drawings' , 0)
        
        return ctx

    def get(self, request):
        # ctx = self.financial_sataements_by_pandas()
        ctx = self.financial_sataements_by_sql()
        ctx['start_date'] = request.user.fs_reporting_period.start_date
        ctx['end_date'] = request.user.fs_reporting_period.end_date

        return render(request , self.template_name  , ctx)
      



class ExportJournal(LoginRequiredMixin , View):
    def get(self , request):
        # Create the HttpResponse object with the appropriate CSV header.
        owner= request.user
        journal = Journal.objects.filter(account__owner=owner).all()

        response = StreamingHttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="journal{}.csv"'.format(timezone.now())

        writer = csv.writer(response)
        writer.writerow(['Date', 'Account', 'balance', 'transaction type' , 'comment'])
        
        for row in journal:
            writer.writerow([row.date , row.account , row.balance , row.transaction_type , row.comment ])

        return response

class Dashboard(LoginRequiredMixin,ConfigRequiredMixin, View):
    def pie_plot(self, labels, values, title):
        fig = go.Figure(data=[go.Pie(labels=labels, values= values)] )
        fig.update_layout(title_text= title)
        return fig.to_html(full_html=False, include_plotlyjs=False)


    def get(self, request):
        owner =  request.user
        query = Q(journal__account__owner=owner)
        query.add(Q(date__lte=request.user.fs_reporting_period.end_date), Q.AND)
        total_transaction = Transaction.objects.filter(query).distinct().count()
        total_accounts = Accounts.objects.filter(owner=owner).count()

        query2 = Q(account__owner=owner)
        query2.add(Q(transaction__date__lte=request.user.fs_reporting_period.end_date), Q.AND)
        avg_transaction = Journal.objects.filter(query2).distinct().aggregate(Avg("balance")) 

    
        data = Accounts.my_objects.accounts_type_balances(request.user.id, request.user.fs_reporting_period.end_date)
        accounts_dic = {key:value for value, key in data}

     
        income = accounts_dic.get("Revenue", 0) - accounts_dic.get("Expenses", 0)
        equity = accounts_dic.get("Investment", 0) + income - accounts_dic.get("Drawings", 0)        
        # revenue vs expense
        revenues_expenses_fig = self.pie_plot(
            ['Revenues','expenses'],
            [accounts_dic.get("Revenue", 0), accounts_dic.get("Expenses",0)],
            'Revenues vs expenses'
        )


        # investment vs drawings'
        investment_drwaings_fig = self.pie_plot(
            ['Investment','Drawings'],
            [accounts_dic.get("Investment", 0), accounts_dic.get("Drawings", 0)],
            'Investment vs Drawings'
        )

        # total accounts
        fig3 = go.Figure([go.Bar(x=list(accounts_dic.keys()) , y=list(accounts_dic.values()))] )
        fig3.update_layout(title_text='accounts type')
        # accounts_fig = plotly.offline.plot(fig3, auto_open = False, output_type="div")
        accounts_fig =  fig3.to_html(full_html=False, include_plotlyjs=False)

        #cash_flow
        cash_flow = Accounts.my_objects.cash_flow(owner)
        cash_inflow = cash_flow.query('cash_flow == "Cash Inflow"')
        cash_outflow = cash_flow.query('cash_flow == "Cash Outflow"')

        cash_flow_fig = go.Figure(data=[
            go.Bar(name='Cash Inflow', x=cash_inflow['year_month'], y=cash_inflow['balance']),
            go.Bar(name='Cash Outflow', x=cash_outflow['year_month'], y=cash_outflow['balance'])
        ])
        # Change the bar mode
        cash_flow_fig.update_layout(barmode='group', title_text='Cash Flow')
        cash_flow_fig =  cash_flow_fig.to_html(full_html=False, include_plotlyjs=False)

        account_form = AccountForm(user=owner)

        ctx = {
            "total_transaction" : total_transaction , 
            "total_accounts" : total_accounts  , 
            "avg_transaction" : avg_transaction , 
            "revenues_expenses_fig" : revenues_expenses_fig , 
            "investment_drwaings_fig" : investment_drwaings_fig , 
            "equity" : equity  , 
            "accounts_fig" : accounts_fig , 
            "account_form" : account_form ,
            "start_date": request.user.fs_reporting_period.start_date,
            "end_date": request.user.fs_reporting_period.end_date,
            "cash_flow_fig": cash_flow_fig
        }

        return render(request , "sole_proprietorship/dashboard.html"  , ctx)




def my_custom_sql(request):
    with connection.cursor() as cursor:
        print(request.user.id)
        # cursor.execute("SELECT * FROM sole_proprietorship_journal where owner_id = %s " , [request.user.id]  )
        # row = cursor.fetchall()
        cursor.execute(""" 
         SELECT   account_type , account  , normal_balance , sum(helper) as balance FROM (
                                                SELECT * ,
                                                CASE
                                                    WHEN j.transaction_type = a.normal_balance Then  j.balance
                                                    ELSE ( -1 * j.balance)
                                                END as helper 
                                                FROM sole_proprietorship_journal as j
                                                JOIN sole_proprietorship_accounts as a
                                                on j.account_id = a.id
                                                where j.owner_id = %s
                                )
GROUP by account_type , account
ORDER by balance DESC



                                                """ , [request.user.id])
        row = list(cursor)
    # row = Journal.objects.raw('SELECT * FROM sole_proprietorship_journal ' )
    return HttpResponse(row)


def render_to_pdf(template_src, context_dict={}):
    """
    src: https://github.com/divanov11/django-html-2-pdf/blob/master/htmltopdf/app/views.py

    https://www.youtube.com/watch?v=5umK8mwmpWM
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


#Opens up page as PDF
class ViewPDF(FinancialStatements):
    def get(self, request, *args, **kwargs):
        ctx = self.financial_sataements_by_sql()
        ctx['start_date'] = request.user.fs_reporting_period.start_date
        ctx['end_date'] = request.user.fs_reporting_period.end_date
        ctx['company_name'] = request.user.fs_reporting_period.company_name or 'AYBA'

        pdf = render_to_pdf('sole_proprietorship/FS_report.html', ctx)
        return HttpResponse(pdf, content_type='application/pdf')



# class PrintView(FinancialStatements, PDFView):

#     def get_context_data(self, *args, **kwargs):
#         """Pass some extra context to the template."""
#         return self.financial_sataements_by_sql()


class TransactionsPDFView(LoginRequiredMixin, View):
    template_name = 'sole_proprietorship/transaction_pdf.html'

    @property
    def report_header(self):
        header = {
            'start_date': self.request.user.fs_reporting_period.start_date,
            'end_date' : self.request.user.fs_reporting_period.end_date
        }

        if self.request.session.get('export_journal'):
            if self.request.session.get('export_journal', {}).get('date__gte'):
                header['start_date'] = self.request.session.get('export_journal').get('date__gte')
 
            if self.request.session.get('export_journal', {}).get('date__lte'):
                header['end_date'] = self.request.session.get('export_journal').get('date__lte')
          
        return header

    def get(self, request, *args, **kwargs):
        f = TransactionFilter(request.session.get('export_journal'))
        queryset = f.qs.prefetch_related(
            'journal_set' , 'journal_set__account'
        ).filter(journal__account__owner=request.user).distinct().order_by(
            'id',
            'date'        
        )

        pdf = render_to_pdf(self.template_name, {'transaction_list': queryset, 'request': request, **self.report_header})
        return HttpResponse(pdf, content_type='application/pdf')


class ExportFainacialStatementsToExcel(FinancialStatements):
    def get(self , request):
        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = f'attachment; filename="Faniacial_statments{timezone.now()}.xlsx"'

        workbook = xlsxwriter.Workbook(response)
        worksheet = workbook.add_worksheet()
        bold = workbook.add_format({'bold': True})
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 20)

        # Add a bold format to use to highlight cells.
        bold = workbook.add_format({'bold': True})

        
        worksheet.write('A1', 'Business Information System', bold)
        worksheet.write('A2', 'Instructor Dr.Mona Ganna', bold)
        worksheet.write('A3', 'Student: Ahmed Maher Fouzy Mohamed Salam', bold)
        worksheet.write('A5' , "Trial Balance" , bold)
        worksheet.write('B6' , "Debit" , bold)
        worksheet.write('C6' , "Credit" , bold)

        
        data = self.financial_sataements_by_sql()
        row = 6
        # Trial Balance
        for  account_type , account , normal_balance , balance in data["data"]:
            worksheet.write(row , 0 , account)
            if normal_balance == "Debit":
                worksheet.write(row , 1 , balance)
            else:
                worksheet.write(row , 2 , balance)

            row += 1
        worksheet.write(row , 0 , "Total")
        worksheet.write_formula(row , 1 , f"=sum(B7:B{row})")
        worksheet.write_formula(row , 2 , f"=sum(C7:C{row})")
        
        #Net income statement
        row += 2
        worksheet.write(row , 0  , "Net income statement" , bold)
        row += 1
        worksheet.write(row , 1  , "Expenses" , bold)
        worksheet.write(row , 2 ,  "Revenue" , bold)

        row += 1 
        for account_type , account , normal_balance , balance in data["data"]:
            if account_type == "Expenses" or account_type == "Revenue":
                worksheet.write(row , 0 , account)
                if account_type == "Expenses":
                    worksheet.write(row , 1 , balance)
                else:
                    worksheet.write(row , 2 , balance)
                row += 1

        worksheet.write(row , 0 , "Total")
        worksheet.write(row , 1 , data.get("Expenses" , 0))
        worksheet.write(row , 2 , data.get("Revenue" , 0))
        worksheet.write(row + 1 , 0 , "Net Loss" if data.get("Expenses" , 0) > data.get("Revenue" , 0) else "Net Income")
        worksheet.write(row + 1 , 2 ,  data.get("net_income" , 0) )
        # Owner's equity statements
        row += 3
        worksheet.write(row , 0 , "Owner's equity statements" , bold)
        worksheet.write(row +1 , 0 , "Owner's capital investment")
        worksheet.write(row +1 , 2 ,  data.get("Investment", 0))

        worksheet.write(row +2 , 0 , "Add net income" if data.get("net_income", 0) else "Subtract net loss")
        worksheet.write(row +2 , 1 , data.get("net_income", 0))

        worksheet.write(row +3 , 0 , "Less: Drawings")
        worksheet.write(row +3 , 1 , data.get("Drawings" , 0))

        worksheet.write(row +4 , 0 , "Owner's Equity")
        worksheet.write(row +4 , 2 , data.get("equity" , 0))

        row += 2
        #Finacial Statments
    
        row += 6
        worksheet.write(row , 0 , "Financial Statement" , bold)
        worksheet.write(row +1, 1 , "Assest" , bold)
        row += 1
        for account_type , account , normal_balance , balance in data["data"]:
            if account_type == "Assest":
                worksheet.write(row , 0 , account)
                worksheet.write(row , 2 , balance)
                row += 1

        worksheet.write(row , 0 , "Total Assest" )
        worksheet.write(row , 2 , data.get("Assest" , 0) )

        worksheet.write(row +1, 1 , "liabilities" , bold)
        row += 2
        for account_type , account , normal_balance , balance in data["data"]:
            if account_type == "liabilities":
                worksheet.write(row , 0 , account)
                worksheet.write(row , 2 , balance)
                row += 1
        worksheet.write(row , 0 , "Total liabilities" )
        worksheet.write(row , 2 , data.get("liabilities" , 0) )

        worksheet.write(row  + 1 , 1 , "Owner's Equity" )
        worksheet.write(row  + 2 , 0 , "Owner's Equity" )

        worksheet.write(row  + 2 , 2 , data.get("equity" , 0) )

        
        worksheet.write(row  + 3 , 0 , "Total Liabilities and Owner's Equity" , bold )
        worksheet.write(row  + 3 , 2 , data.get("equity" , 0) + data.get("liabilities" ,0) )


        workbook.close()
      

        return response

class AccountsImport(LoginRequiredMixin , View):
    def get(self , request):
        return render(request , "sole_proprietorship/import_accounts.html" , {"form":UploadFileForm()})
    
    @transaction.atomic
    def post(self , request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = form.cleaned_data['file']
            df = pd.read_excel(excel_file)
            accounts_to_create = []
            for dic in df.to_dict('records'):
                accounts_to_create.append(
                    Accounts(
                            owner=request.user , 
                            account=dic["account"] ,
                            normal_balance = dic["normal_balance"] , 
                            account_type = dic["account_type"]
                            )
                )
            Accounts.objects.bulk_create(accounts_to_create)
            messages.success(request, 'Your Chat of Accounts Imported Successfuly')
        return HttpResponseRedirect(reverse("sole_proprietorship:all"))



# class PivotTable(LoginRequiredMixin , View):
    
#     def get(self , request):
#         with connection.cursor() as cursor:

#             query = cursor.execute("""SELECT date , account , sum(helper) as Balance , normal_balance , transaction_type , account_type FROM (
#                                             SELECT * ,
#                                             CASE
#                                                 WHEN j.transaction_type = a.normal_balance Then  j.balance
#                                                 ELSE ( -1 * j.balance)
#                                             END as helper 
#                                             FROM sole_proprietorship_journal as j
#                                             JOIN sole_proprietorship_accounts as a
#                                             on j.account_id = a.id
#                                             Join sole_proprietorship_transaction as t
#                                             ON t.id = j.transaction_id
#                                             where a.owner_id = %s			
#                                                                                                         )
#                             GROUP by date , account """ , [request.user.id] )
#             df = pd.DataFrame(query.fetchall() , columns=["date" , "account" , "Balance" , "normal_balance" , "transaction_type" , "account_type"])
#         # owner=request.user
#         # accounts = Accounts.objects.filter(owner=owner).all().values()
#         # journal = Journal.objects.filter(owner=owner).all().values()
#         # df = prepare_data_frame(journal , accounts)
#         pivot = pivot_ui(df)
#         with open(pivot.src) as t:
#             r = t.read()
#         ctx = {
#             "result": r
#         }
#         return render(request , "sole_proprietorship/test.html" , ctx)



class ReportingPeriodConfigView(LoginRequiredMixin , View):
    template_name = "sole_proprietorship/reporting_period_form.html"

    def get(self , request):
        owner = request.user
        data = {
            "start_date":None,
            "end_date":None
        }
        if hasattr(owner, 'fs_reporting_period'):
            data["start_date"] = owner.fs_reporting_period.start_date
            data["end_date"] = owner.fs_reporting_period.end_date
            data['company_name'] = owner.fs_reporting_period.company_name

        form = ReportingPeriodConfigForm(initial=data)

        ctx = {
            "form":form
        }
        return render(request , self.template_name , ctx)
    
    def post(self, request):
        form = ReportingPeriodConfigForm(request.POST)
        if form.is_valid():
            f = form.save(commit=False)
            f.owner = request.user
            f.save()
            messages.success(request, 'Reporting Period Config Has been set correctly')

        return HttpResponseRedirect(reverse("sole_proprietorship:home"))


class TransactionUpdateView(LoginRequiredMixin, View):
    template_name = 'sole_proprietorship/transaction_update.html'
    helper = TransactionFormSetHelper()

    def get(self, request, pk, *args, **kwargs):
        queryset = Transaction.objects.filter(journal__account__owner=request.user, pk=pk).distinct()
        transaction = get_object_or_404(queryset)
        formset = TransactionFormSet(instance=transaction)
        return render(request, self.template_name, {'formset': formset, 'helper': self.helper})

    @transaction.atomic
    def post(self, request, pk,  *args, **kwargs):
        queryset = Transaction.objects.filter(journal__account__owner=request.user, pk=pk).distinct()
        transaction = get_object_or_404(queryset)
        formset = TransactionFormSet(request.POST, request.FILES, instance=transaction)
        if formset.is_valid():
            formset.save()
            
            messages.success(request, 'Your transaction has been updated successfully')
            return HttpResponseRedirect(reverse("sole_proprietorship:transaction_list"))
        return render(request, self.template_name, {'formset': formset, 'helper': self.helper})



class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    model = Transaction
    
    def get_queryset(self):
        qs = super().get_queryset().filter(journal__account__owner=self.request.user).distinct()
        return qs




class LedgerView(LoginRequiredMixin, ConfigRequiredMixin,  View):
    template_name = 'sole_proprietorship/ledger.html'

    def get(self, request, *args, **kwargs):
        form = LedgerFilterForm(request=request)
        return render(request, self.template_name, {'form':form})



class FetchLedgerView(LoginRequiredMixin, View):
    def get(self, request):
        ctx = {
            'begginingBalance': Accounts.my_objects.beginning_balance(owner_id=request.user.id, 
                end_date= request.GET.get('start_date'),
                account =  request.GET.get('account')
            ),
            'data': Accounts.my_objects.ledger(owner_id = request.user.id,
             account=request.GET.get('account'),
            start_date=request.GET.get('start_date'),
            end_date= request.GET.get('end_date'))
        }
        return JsonResponse(ctx)


class AccountOverTimeView(LoginRequiredMixin, View):
    def get(self, request):
        data = Accounts.my_objects.account_over_time(
                owner_id = request.user.id,
                account=request.GET.get('account'),
                start_date= request.user.fs_reporting_period.start_date,
                end_date= request.user.fs_reporting_period.end_date
        )

        df = pd.DataFrame(data, columns=['Date', 'Amount'])
        fig = go.Figure()
        fig.add_trace(
                go.Scatter(x=list(df.Date), y=list(df.Amount))
        )
        account_name = Accounts.objects.get(owner=request.user, pk=request.GET.get('account')).account
        fig.update_layout(
            title_text=f"{account_name} balance over the time"
        )
        # Add range slider
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1,
                            label="1m",
                            step="month",
                            stepmode="backward"),
                        dict(count=6,
                            label="6m",
                            step="month",
                            stepmode="backward"),
                        dict(count=1,
                            label="YTD",
                            step="year",
                            stepmode="todate"),
                        dict(count=1,
                            label="1y",
                            step="year",
                            stepmode="backward"),
                        dict(step="all")
                    ])
                ),
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )
        account_over_time_fig = fig.to_html(full_html=False, include_plotlyjs=False)

        ctx = {
            'account_over_time_fig': mark_safe(account_over_time_fig)
        }

        return JsonResponse(ctx)


class DetailAccountTypeView(LoginRequiredMixin, View):
    def get(self, request):
        print('account_type', request.GET.get('account_type'))
        # if request.GET.get('account_type') in ['']
        # we can do validation for input to prevent SQL injection but i realize Django Take care of this for us
        data = Accounts.my_objects.account_type_account_balance(
                owner_id = request.user.id,
                account_type=request.GET.get('account_type'),
                end_date= request.user.fs_reporting_period.end_date
        )

        df = pd.DataFrame(data, columns=['account_type', 'account', 'balance'])
        fig = go.Figure(go.Bar(
            x=df['balance'],
            y=df['account'],
            orientation='h')
        )

        total = df['balance'].sum()
        df['%'] = round(df['balance'] / total  * 100, 2)
        df.loc[len(df)] =  ['', 'Total', total, 100] 
        df_fig = ff.create_table(df.iloc[: , 1:])
        
        
    

        fig.update_layout(
            title_text=f"{request.GET.get('account_type')} accounts and their balance"
        )
        accounts_fig = fig.to_html(full_html=False, include_plotlyjs=False)

        ctx = {
            'accounts_fig': mark_safe(accounts_fig),
            'df_fig': mark_safe(df_fig.to_html(full_html=False, include_plotlyjs=False))
        }

        return JsonResponse(ctx)

class FetchAccounts(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):
        queryset = Accounts.objects.filter(
              owner= self.request.user
            ).values(
                'id',
                'account',
            )        
        return JsonResponse(
                    [   { 
                            'id': account['id'],
                            'name': account['account'],
                        }

                         for account in queryset
                    ], safe=False
                )

class FinancialAnalysisView(LoginRequiredMixin, ConfigRequiredMixin, View):
    template_name = 'sole_proprietorship/financial_analysis.html'
    message_warning = """
    In oder to use this feature you should complete all fields for classification on Account table
    """
    
    def get(self, request, *args, **kwargs):
        if Accounts.objects.filter(owner = request.user, classification__isnull = True).count()  > 0:
            messages.warning(request, self.message_warning)

        ctx = Accounts.financial.analysis(request.user)
        ctx['start_date'] = request.user.fs_reporting_period.start_date
        ctx['end_date'] = request.user.fs_reporting_period.end_date
        
        return render(request, self.template_name, ctx)