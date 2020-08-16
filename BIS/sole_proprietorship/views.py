from .models import Journal , Accounts
from .owner import OwnerListView, OwnerCreateView, OwnerUpdateView, OwnerDeleteView

class AccountsListView(OwnerListView):
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
    model = Journal
    # By convention:
    # template_name = "app_name/model_list.html"


class JournalCreateView(OwnerCreateView):
    model = Journal
    fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

class JournalUpdateView(OwnerUpdateView):
    model = Journal
    fields = ['account', 'date' , 'balance' , "transaction_type" , "comment"]

class JournalDeleteView(OwnerDeleteView):
    model = Journal


