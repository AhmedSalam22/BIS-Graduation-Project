from django.urls import path, reverse_lazy
from . import views

app_name='sole_propritorship'
urlpatterns = [
    path('', views.AccountsListView.as_view(), name='all'),
    path('accounts/create', 
        views.AccountsCreateView.as_view(success_url=reverse_lazy('sole_propritorship:all')), name='accounts_create'),
    path('accounts/<int:pk>/update', 
        views.AccountsUpdateView.as_view(success_url=reverse_lazy('sole_propritorship:all')), name='accounts_update'),
    path('accounts/<int:pk>/delete', 
        views.AccountsDeleteView.as_view(success_url=reverse_lazy('sole_propritorship:all')), name='accounts_delete'),
]

# We use reverse_lazy in urls.py to delay looking up the view until all the paths are defined
