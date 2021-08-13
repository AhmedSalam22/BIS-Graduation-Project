from django.urls import path, reverse_lazy
from . import views
from django.views.decorators.cache import cache_page

app_name = "Customer_Sales"
urlpatterns = [
    path('add_customer' , views.CoustomerView.as_view(), name="add_customer" ),
    # path('', cache_page(60 * 60)(views.Home.as_view()), name='home')
    path('', views.Home.as_view(), name='home'),
    path('customers_list', views.CustomerListView.as_view(), name='customer_list'),
    path('customer_delete/<int:pk>', views.CustomerDeleteView.as_view(success_url=reverse_lazy('Customer_Sales:customer_list')), name='customer_delete'),


]
