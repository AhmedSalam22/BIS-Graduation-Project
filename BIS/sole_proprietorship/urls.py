from django.urls import path, reverse_lazy
from django.views.generic import TemplateView
from . import views

app_name='sole_proprietorship'
urlpatterns = [
    path("" , TemplateView.as_view(template_name= "sole_proprietorship/index.html")),
    path('/accounts', views.AccountsListView.as_view(), name='all'),
    path('/accounts/create', 
        views.AccountsCreateView.as_view(success_url=reverse_lazy('sole_proprietorship:all')), name='accounts_create'),
    path('/accounts/<int:pk>/update', 
        views.AccountsUpdateView.as_view(success_url=reverse_lazy('sole_proprietorship:all')), name='accounts_update'),
    path('/accounts/<int:pk>/delete', 
        views.AccountsDeleteView.as_view(success_url=reverse_lazy('sole_proprietorship:all')), name='accounts_delete'),
    # Journal
    path('/journal', views.JournalListView.as_view(), name='journal_all'),
    path('/journal/create', 
        views.JournalCreateView.as_view(success_url=reverse_lazy('sole_proprietorship:journal_all')), name='journal_create'),
    path('/journal/<int:pk>/update', 
        views.JournalUpdateView.as_view(success_url=reverse_lazy('sole_proprietorship:journal_all')), name='journal_update'),
    path('/journal/<int:pk>/delete', 
        views.JournalDeleteView.as_view(success_url=reverse_lazy('sole_proprietorship:journal_all')), name='journal_delete'),
    path("/financialstatements" ,views.FinancialStatements.as_view() , name="financialstatements" )
]

# We use reverse_lazy in urls.py to delay looking up the view until all the paths are defined
