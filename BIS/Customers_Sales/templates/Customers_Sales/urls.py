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
    path('update_customer/<int:pk>', views.CustomerUpdateView.as_view(success_url=reverse_lazy('Customer_Sales:customerlist')), name='customer_update'),
    path('customerdetail/<int:pk>', views.CustomerDetailView.as_view(), name="customer_detail"),
    path('add_phone/<int:customer_id>', views.AddPhoneView.as_view(), name='add_phone'),
    path('add_email/<int:customer_id>', views.AddEmailView.as_view(), name='add_email'),
    path('add_address/<int:customer_id>', views.AddAddressView.as_view(), name='add_address'),
    path('add_note/<int:customer_id>', views.AddNoteView.as_view(), name='add_note'),
    path('update_phone/customer/<int:customer_pk>/phone/<int:pk>', views.CustomerPhoneUpdateView.as_view(), name='update_phone'),
    path('update_adress/customer/<int:customer_pk>/address/<int:pk>', views.CustomerAddressUpdateView.as_view(), name='update_address'),
    path('update_email/customer/<int:customer_pk>/email/<int:pk>', views.CustomerEmailUpdateView.as_view(), name='update_email'),
    path('update_note/customer/<int:customer_pk>/note/<int:pk>', views.CustomerNoteUpdateView.as_view(), name='update_note'),
    path('delete_phone/customer/<int:customer_pk>/phone/<int:pk>', views.CustomerPhoneDeleteView.as_view(), name='delete_phone'),
    path('delete_email/customer/<int:customer_pk>/email/<int:pk>', views.CustomerEmailDeleteView.as_view(), name='delete_email'),
    path('delete_address/customer/<int:customer_pk>/address/<int:pk>', views.CustomerAddressDeleteView.as_view(), name='delete_address'),
    path('delete_note/customer/<int:customer_pk>/note/<int:pk>', views.CustomerNoteDeleteView.as_view(), name='delete_note'),


]
