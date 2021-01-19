from django.urls import path , include , reverse_lazy
from inventory import views

app_name = "inventory"
urlpatterns = [
    path("" , views.HomeView.as_view() , name="home"),
    path('create_term' , views.CreateTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="create_term" ),
    path('update_term/<int:pk>' , views.UpdateTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="update_term" ),
    path('list_term' , views.ListTermView.as_view() , name="list_term" ), 
    path('delete_term/<int:pk>' , views.DeleteTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="delete_term" ),
    path('create_purchase' , views.CreatePurchaseInventoryView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="create_purchase" ),
    path('list_inventory' , views.ListInventoryView.as_view() , name="list_inventory") , 
    path('detail_inventory/<int:pk>' , views.DetailInventoryView.as_view() , name="detail_inventory" ),
    path('create_purchase_return/<int:pk>' , views.CreatePurchaseReturnView.as_view() , name="create_purchase_return"),
    path('list_purchase' , views.ListPurchaseInventoryView.as_view() , name="list_purchase") ,
    path('detail_purchase/<int:pk>' , views.DetailPurchaseInventoryView.as_view() , name="detail_purchase") , 


]
