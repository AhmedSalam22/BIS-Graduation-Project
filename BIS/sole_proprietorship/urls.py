from django.urls import path, reverse_lazy
from django.views.generic import TemplateView
from . import views
from django.views.decorators.cache import cache_page

app_name='sole_proprietorship'
urlpatterns = [
    path("" , TemplateView.as_view(template_name= "sole_proprietorship/index.html") , name = "home"),
    path('accounts', views.AccountsListView.as_view(), name='all'),
    path('accounts/create', 
        views.AccountsCreateView.as_view(success_url=reverse_lazy('sole_proprietorship:all')), name='accounts_create'),
    path('accounts/<int:pk>/update', 
        views.AccountsUpdateView.as_view(success_url=reverse_lazy('sole_proprietorship:all')), name='accounts_update'),
    path('accounts/<int:pk>/delete', 
        views.AccountsDeleteView.as_view(success_url=reverse_lazy('sole_proprietorship:all')), name='accounts_delete'),
    # Journal
    path('journal/create', 
        views.JournalCreateView.as_view(success_url=reverse_lazy('sole_proprietorship:transaction_list')), name='journal_create'),
    path('journal/<int:pk>/update', 
        views.JournalUpdateView.as_view(success_url=reverse_lazy('sole_proprietorship:transaction_list')), name='journal_update'),
    path('journal/<int:pk>/delete', 
        views.JournalDeleteView.as_view(success_url=reverse_lazy('sole_proprietorship:transaction_list')), name='journal_delete'),
    path("financialstatements" ,views.FinancialStatements.as_view() , name="financialstatements" ) , 
    path("export_journal" , views.ExportJournal.as_view() , name = "export_journal") ,
    path("dashboard" , views.Dashboard.as_view() , name ="dashboard") ,
    path("DownloadFS" , views.ViewPDF.as_view() , name = "fsdonwload") , 
    path('DownloadXLSX' , views.ExportFainacialStatementsToExcel.as_view() ,name="excelDownload"),
    path('accounts/import' , views.AccountsImport.as_view() , name="ImportAccounts" ) ,
    # path('pivotTable' , views.PivotTable.as_view()  , name="pivottable"),
    path('ReportingPeriodConfig' ,views.ReportingPeriodConfigView.as_view(), name="ReportingPeriodConfig"),
    path('transactions', views.TransactionListView.as_view(), name='transaction_list'),
    path('transaction/<int:pk>/update', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transaction/<int:pk>/delete', 
        views.TransactionDeleteView.as_view(success_url=reverse_lazy('sole_proprietorship:transaction_list')), name='transaction_delete'),
    path('ledger/', views.LedgerView.as_view(), name='ledger'),
    path('fetch_ledger', views.FetchLedgerView.as_view(), name='fetch_ledger'),
    path('export_transactions_csv', views.ExportTrsanctionView.as_view(), name='export_transactions_csv'),
    path('export_transactions_pdf', views.TransactionsPDFView.as_view(), name='export_transactions_pdf'),
    path('account_over_time', views.AccountOverTimeView.as_view(), name='account_over_time'),
    path('DetailAccountTypeView', views.DetailAccountTypeView.as_view(), name='detail_account_type'),
    path('fetch_accounts', views.FetchAccounts.as_view(), name='fetch_accounts'),
    path('financial_analysis', views.FinancialAnalysisView.as_view(), name='financial_analysis'),



]

# We use reverse_lazy in urls.py to delay looking up the view until all the paths are defined
