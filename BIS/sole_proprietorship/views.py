from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import connection
from django.http import HttpResponse , HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import render
from .models import Journal , Accounts
from .owner import OwnerListView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView
from .forms import JournalForm , JournalFilter , AccountForm  , UploadFileForm , create_form
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
from pivottablejs import pivot_ui
from home.formsetview import MyFormSetView
from django.contrib import messages



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



class AccountsCreateView(OwnerCreateView):
    model = Accounts
    fields = ['account', 'normal_balance' , 'account_type']

class AccountsUpdateView(OwnerUpdateView):
    model = Accounts
    fields = ['account', 'normal_balance' , 'account_type']

class AccountsDeleteView(OwnerDeleteView):
    model = Accounts


class JournalListView( LoginRequiredMixin , FilterView):
    paginate_by = 10
    model = Journal
    template_name = "sole_proprietorship/journal_list.html"
    filterset_class = JournalFilter

    def get_queryset(self):
        qs = super(JournalListView, self).get_queryset()
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # we don't this line since we use FilterView which do this automatically for you
        # context["filter"] = JournalFilter(data=self.request.GET , queryset = get_queryset() , user=self.request.user)
        with connection.cursor() as cursor:
            cursor.execute(""" 
                  SELECT   sum(helper) as balance ,  normal_balance  FROM (
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
        GROUP by normal_balance 
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


class JournalCreateView(LoginRequiredMixin , MyFormSetView):
    fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]
    template_name = 'sole_proprietorship/journal_form.html'
    form_class = None

    def get_form_class(self , request):
        """
        Returns the form class to use with the formset in this view
        """
        self.form_class = create_form(request.user) #overriding
        print("asda:" , request.user)
        return self.form_class

    # لكى يستطيع ان يتعامل مع الحسابات التى يمتلكها فقط
    # def get_form(self, form_class=JournalForm):
    #     print("sdfsdfdsfsf")
    #     form = super(OwnerCreateView,self).get_form(form_class) #instantiate using parent
    #     form.fields['account'].queryset = Accounts.objects.filter(owner=self.request.user)
    #     return form

    # print(super(JournalCreateView , self).get_form(**kwargs))
    def formset_valid(self, formset):
        # do whatever you'd like to do with the valid formset
        messages.success(self.request, 'Your Transaction Was Created Succesffuly')
        for form in formset:
            object = form.save(commit=False)
            object.owner = self.request.user
            object.save()
        return super(JournalCreateView, self).formset_valid(formset)
    # def form_valid(self, form):
    #     object = form.save(commit=False)
    #     object.owner = self.request.user
    #     object.save()
    #     return super(OwnerCreateView, self).form_valid(form)

class JournalUpdateView(OwnerUpdateView):
    model = Journal
    fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

class JournalDeleteView(OwnerDeleteView):
    model = Journal





class FinancialStatements(LoginRequiredMixin, View):
    def financial_sataements_by_pandas(self):
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
                                                    where j.owner_id = %s
                                    )
    GROUP by account_type , account
    ORDER by balance DESC
                                                    """ , [self.request.user.id])

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
            'Total_Credit' : total_credit , 
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

        return render(request , "sole_proprietorship/financial_statements.html"  , ctx)
      



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
            query = cursor.execute("""SELECT date , account , sum(helper) as Balance , account_id FROM (
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
                            GROUP by date , account """ , [request.user.id] )
            data = pd.DataFrame(query.fetchall() , columns=["date" , "account" , "balance_negative" , "account_id"])
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
        account_form = AccountForm(user=owner)
        q2 = data.query("account_id == '{}' ".format(request.GET.get("account") , None))
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
            "line_fig": line_fig , 
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
        # ctx = self.financial_sataements_by_pandas()
        ctx = self.financial_sataements_by_sql()
        pdf = render_to_pdf('sole_proprietorship/FS_report.html', ctx)
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
    
    def post(self , request):
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data['file']
            df = pd.read_excel(file)
            for dic in df.to_dict('records'):
                account = Accounts(owner=request.user , 
                                    account=dic["account"] ,
                                    normal_balance = dic["normal_balance"] , 
                                    account_type = dic["account_type"] 
                                     )
                account.save()
        messages.success(request, 'Your Chat of Accounts Imported Successfuly')
        return HttpResponseRedirect(reverse("sole_proprietorship:all"))



class PivotTable(LoginRequiredMixin , View):
    
    def get(self , request):
        with connection.cursor() as cursor:

            query = cursor.execute("""SELECT date , account , sum(helper) as Balance , normal_balance , transaction_type , account_type FROM (
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
                            GROUP by date , account """ , [request.user.id] )
            df = pd.DataFrame(query.fetchall() , columns=["date" , "account" , "Balance" , "normal_balance" , "transaction_type" , "account_type"])
        # owner=request.user
        # accounts = Accounts.objects.filter(owner=owner).all().values()
        # journal = Journal.objects.filter(owner=owner).all().values()
        # df = prepare_data_frame(journal , accounts)
        pivot = pivot_ui(df)
        with open(pivot.src) as t:
            r = t.read()
        ctx = {
            "result": r
        }
        return render(request , "sole_proprietorship/test.html" , ctx)
