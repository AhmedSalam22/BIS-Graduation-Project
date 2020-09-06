from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from .models import Journal , Accounts
from .owner import OwnerListView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import JournalForm
import pandas as pd
import numpy as np
import csv
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Avg
import plotly.graph_objects as go
import plotly
from .forms import AccountForm
import plotly.express as px
from easy_pdf.views import PDFTemplateView , PDFTemplateResponseMixin
from django.db import connection





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


class AccountsListView(OwnerListView):
    paginate_by = 10

    model = Accounts
    # By convention:
    # template_name = "app_name/model_list.html"


class AccountsCreateView(OwnerCreateView):
    model = Accounts
    fields = ['account', 'normal_balance' , 'account_type']

class AccountsUpdateView(OwnerUpdateView):
    model = Accounts
    fields = ['account', 'normal_balance' , 'account_type']

class AccountsDeleteView(OwnerDeleteView):
    model = Accounts


class JournalListView(OwnerListView):
    paginate_by = 10
    model = Journal
    # By convention:
    # template_name = "app_name/model_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        with connection.cursor() as cursor:
            cursor.execute(""" 
                            SELECT sum(balance) , transaction_type FROM (
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
                            GROUP by transaction_type
                                                    """ , [self.request.user.id])
            row = list(cursor.fetchall())
            print(row)
        try:
            context[row[0][1]] = row[0][0]
            context[row[1][1]] = row[1][0]
        except IndexError:
            context["Debit"] = 0
            context["Credit"] = 0

        return context


class JournalCreateView(OwnerCreateView):
    model = Journal
    fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]
    # لكى يستطيع ان يتعامل مع الحسابات التى يمتلكها فقط
    def get_form(self, form_class=JournalForm):
        form = super(OwnerCreateView,self).get_form(form_class) #instantiate using parent
        form.fields['account'].queryset = Accounts.objects.filter(owner=self.request.user)
        return form

class JournalUpdateView(OwnerUpdateView):
    model = Journal
    fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

class JournalDeleteView(OwnerDeleteView):
    model = Journal

class FinancialStatements(LoginRequiredMixin, View):
    def get(self, request):
        owner=self.request.user
        # Accounts.objects.filter(owner=owner)[0].journal_set.values()
        #Accounts.objects.filter(owner=owner).all().values()

        accounts = Accounts.objects.filter(owner=owner).all().values()
        journal = Journal.objects.filter(owner=owner).all().values()

        try:
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

            # df_accounts.to_csv('accounts.csv',index=False)
            # df_journal.to_csv('journal.csv',index=False)

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
            return render(request , "sole_proprietorship/financial_statements.html"  , ctx)
        except Exception  as error:
            return HttpResponse("<p><strong>You Should Complete all accounts first to get this feature -- {}</strong><p>".format(error))





class FinancialStatementsPDF(PDFTemplateView):
    template_name = 'sole_proprietorship/FS_report.html'

    def get_context_data(self, *args, **kwargs):
        owner=self.request.user
        # Accounts.objects.filter(owner=owner)[0].journal_set.values()
        #Accounts.objects.filter(owner=owner).all().values()

        accounts = Accounts.objects.filter(owner=owner).all().values()
        journal = Journal.objects.filter(owner=owner).all().values()


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

        # df_accounts.to_csv('accounts.csv',index=False)
        # df_journal.to_csv('journal.csv',index=False)

        ctx = {
            "trial_balance": trial_balance[0].to_html(classes="table") , 
            "debit_credit" : trial_balance[1] , 
            "net_income" : net_income[0].to_html() ,
            "revenue_expenses": net_income[1] , 
            "amount"  : amount , 
            "investment" : investment , 
            "drawings" : drawings ,
            "equity": equity ,
            "assest": assest.to_html(), 
            "total_assest" : total_assest[0] ,
            "liabilities" : liabilities.to_html() ,
            "total_liabilities" : total_liabilities[0]




        }
        return ctx


class ExportJournal(LoginRequiredMixin , View):
    def get(self , request):
        # Create the HttpResponse object with the appropriate CSV header.
        owner= request.user
        journal = Journal.objects.filter(owner=owner).all()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="journal{}.csv"'.format(timezone.now())

        writer = csv.writer(response)
        writer.writerow(['Date', 'Account', 'balance', 'transaction type' , 'comment'])
        
        for row in journal:
            writer.writerow([row.date , row.account , row.balance , row.transaction_type , row.comment ])

        return response

class Dashboard(LoginRequiredMixin , View):
    def get(self, request):
        owner =  request.user
        total_transaction = Journal.objects.filter(owner=owner).count()
        total_accounts = Accounts.objects.filter(owner=owner).count()
        avg_transaction = Journal.objects.filter(owner=owner).aggregate(Avg("balance")) 
        with connection.cursor() as cursor:
            cursor.execute(""" 
                            SELECT sum(helper) as balance,  account_type FROM (
                                                    SELECT * ,
                                                    CASE
                                                        WHEN j.transaction_type = a.normal_balance Then  j.balance
                                                        ELSE ( -1 * j.balance)
                                                    END as helper 
                                                    FROM sole_proprietorship_journal as j
                                                    JOIN sole_proprietorship_accounts as a
                                                    on j.account_id = a.id
                                                    where j.owner_id = %s )
            GROUP by account_type
            ORDER by balance DESC
                                                    """ , [request.user.id])
            row = list(cursor)
            query = cursor.execute("""SELECT date , account , helper FROM (
                                            SELECT * ,
                                            CASE
                                                WHEN j.transaction_type = a.normal_balance Then  j.balance
                                                ELSE ( -1 * j.balance)
                                            END as helper 
                                            FROM sole_proprietorship_journal as j
                                            JOIN sole_proprietorship_accounts as a
                                            on j.account_id = a.id
                                            where j.owner_id = %s 
                            )""" , [request.user.id] )
            data = pd.DataFrame(query.fetchall() , columns=["date" , "account" , "balance_negative"])
            # print(data)
            # data.columns = query.keys()

        accounts_type = [ account[1] for account in row]
        accounts_balance = [account[0] for account in row]

        accounts = ['Assest' , 'Investment' , 'liabilities' , 'Revenue' , 'Expenses' ,'Drawings']
        accounts_dic = {}
        for account in accounts:
            try:
                accounts_dic[account] = accounts_balance[accounts_type.index(account)]
            except ValueError:
                accounts_dic[account] = 0
        # old method using pandas instead of SQL query
        # accounts = Accounts.objects.filter(owner=owner).all().values()
        # journal = Journal.objects.filter(owner=owner).all().values()
        # data = prepare_data_frame(journal , accounts)
        # trial_balance = prepare_trial_balance(data)
        # net_income =  prepare_net_income(data)
        amount = accounts_dic["Revenue"] - accounts_dic["Expenses"]
        # investment ,  drawings = prepare_equity_statement(data)
        equity = accounts_dic["Investment"] + amount - accounts_dic["Drawings"]
        # assest , total_assest , liabilities ,total_liabilities = prepare_finacial_statement(data)
        
        # revenue vs expense
        labels = ['Revenues','expenses']
        values = [accounts_dic["Revenue"], accounts_dic["Expenses"]]
        fig = go.Figure(data=[go.Pie(labels=labels, values= values)] )
        fig.update_layout(title_text='Revenues vs expenses')
        revenues_expenses_fig = plotly.offline.plot(fig, auto_open = False, output_type="div")
        # investment vs drawings
        labels2 = ['Investment','Drawings']
        values2 = [accounts_dic["Investment"], accounts_dic["Drawings"] ]
        fig2 = go.Figure(data=[go.Pie(labels=labels2, values=values2)])
        fig2.update_layout(title_text='Investment vs Drawings')
        investment_drwaings_fig = plotly.offline.plot(fig2, auto_open = False, output_type="div")
        # total accounts
        # q = data.groupby("account_type")["balance_negative"].sum()
        # q.sort_values(ascending=False , inplace=True)
        fig3 = go.Figure([go.Bar(x=accounts_type , y=accounts_balance)] )
        fig3.update_layout(title_text='accounts type')
        accounts_fig = plotly.offline.plot(fig3, auto_open = False, output_type="div")
        #line chart 
        account_form = AccountForm()
        q2 = data.query("account == '{}' ".format(request.GET.get("account_name") , None))
        line_fig = px.line(q2, x="date", y="balance_negative")
        line_fig = plotly.offline.plot(line_fig, auto_open = False, output_type="div")

        ctx = {
            "total_transaction" : total_transaction , 
            "total_accounts" : total_accounts  , 
            "avg_transaction" : avg_transaction , 
            "revenues_expenses_fig" : revenues_expenses_fig , 
            "investment_drwaings_fig" : investment_drwaings_fig , 
            "equity" : equity  , 
            "accounts_fig" : accounts_fig , 
            "account_form" : account_form ,
            "line_fig": line_fig
        }


        return render(request , "sole_proprietorship/dashboard.html"  , ctx)
     


# from django.db import connection

def my_custom_sql(request):
    with connection.cursor() as cursor:
        print(request.user.id)
        # cursor.execute("SELECT * FROM sole_proprietorship_journal where owner_id = %s " , [request.user.id]  )
        # row = cursor.fetchall()
        cursor.execute(""" 
                      SELECT sum(helper) as balance,  account_type FROM (
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
GROUP by account_type
ORDER by balance DESC

                                                """ , [request.user.id])
        row = list(cursor)
    # row = Journal.objects.raw('SELECT * FROM sole_proprietorship_journal ' )

    return HttpResponse(row)