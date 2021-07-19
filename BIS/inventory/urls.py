from django.urls import path , include , reverse_lazy
from inventory import views

app_name = "inventory"
urlpatterns = [
    path("" , views.HomeView.as_view() , name="home"),
    path('create_term' , views.CreateTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="create_term" ),
    path('update_term/<int:pk>' , views.UpdateTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="update_term" ),
    path('list_term' , views.ListTermView.as_view() , name="list_term" ), 
    path('delete_term/<int:pk>' , views.DeleteTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="delete_term" ),
    path('create_purchase' , views.CreatePurchaseInventoryView.as_view(success_url='inventory:detail_purchase') , name="create_purchase" ),
    path('create_inventory' , views.CreateInventoryView.as_view(success_url='inventory:detail_inventory') , name="create_inventory" ),
    path('list_inventory' , views.ListInventoryView.as_view() , name="list_inventory") , 
    path('detail_inventory/<int:pk>' , views.DetailInventoryView.as_view() , name="detail_inventory" ),
    path('delete_inventory/<int:pk>', views.DeleteInventoryView.as_view(success_url=reverse_lazy('inventory:list_inventory')), name='delete_inventory'),
    path('update_inventory/<int:pk>', views.UpdateInventoryView.as_view(success_url='inventory:detail_inventory'), name='update_inventory'),

    path('create_purchase_return/<int:pk>' , views.CreatePurchaseReturnView.as_view() , name="create_purchase_return"),
    path('create_purchase_return/' , views.CreatePurchaseReturnView.as_view() , name="create_purchase_return_no_paramter"),
    path('list_purchase' , views.ListPurchaseInventoryView.as_view() , name="list_purchase") ,
    path('detail_purchase/<int:pk>' , views.DetailPurchaseInventoryView.as_view() , name="detail_purchase") , 
    path('delete_purchase/<int:pk>', views.DeletePurchaseInventoryView.as_view(success_url=reverse_lazy('inventory:list_purchase')), name='delete_purchase'),
    path('purchases_dashboard' , views.PurchasesDashboard.as_view() , name="purchases_dashboard") , 
    path('pay_invoice/<int:pk>' , views.PayInvoicePayView.as_view(success_url=reverse_lazy('inventory:list_purchase')) , name="pay_invoice"),
    path('pay_invoice' , views.PayInvoicePayView.as_view(success_url=reverse_lazy('inventory:list_purchase')) , name="pay_invoice_no_args"),

    path('pay_invoice_delete/<int:pk>' , views.PayInvoiceDeleteView.as_view(success_url=reverse_lazy('inventory:list_purchase')) , name="pay_invoice_delete"),
    path('create_purchase_allowance', views.PurchaseAllowanceView.as_view(success_url='inventory:detail_purchase'), name='create_purchase_allowance'),
    path('create_purchase_allowance/<int:pk>', views.PurchaseAllowanceView.as_view(success_url='inventory:detail_purchase'), name='create_purchase_allowance'),
    path('fetch_inventory_price', views.FetchInventoryPriceView.as_view(), name='fetch_inventory_price'),
    path('create_sales', views.CreateSalesView.as_view(), name='create_sales'),
    path('create_sales_return/<int:sales_pk>/<int:sales_item_pk>', views.CreateSalesReturnView.as_view(), name='create_sales_return_args'),
    path('create_sales_return/', views.CreateSalesReturnView.as_view(), name='create_sales_return'),
    path('create_sales_allowance/<int:sales_pk>', views.CreateSalesAllowanceView.as_view(), name='create_sales_allowance_args'),
    path('create_sales_allowance', views.CreateSalesAllowanceView.as_view(), name='create_sales_allowance'),
    path('create_sales_payment', views.CreateSalesPaymentView.as_view(), name='create_sales_payment'),
    path('create_sales_payment/<int:sales_pk>', views.CreateSalesPaymentView.as_view(), name='create_sales_payment_args'),
    path('sales_list', views.SalesListView.as_view(), name='sales_list'),
    path('delete_sale/<int:pk>', views.SalesDeleteView.as_view(success_url=reverse_lazy('inventory:sales_list')), name='delete_sales'),
    path('sale/<int:pk>', views.SalesDetailView.as_view(), name='sale_detail'),
    path('test' , views.Test.as_view() , name="test"),
    path('PivotTable' , views.PivotTableView.as_view() , name="pivot_table")


]
