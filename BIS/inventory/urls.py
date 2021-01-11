from django.urls import path , include , reverse_lazy
from inventory import views

app_name = "inventory"
urlpatterns = [
    path('create_term' , views.CreateTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="create_term" ),
    path('update_term/<int:pk>' , views.UpdateTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="update_term" ),
    path('list_term/' , views.ListTermView.as_view() , name="list_term" ), 
    path('delete_term/<int:pk>' , views.DeleteTermView.as_view(success_url=reverse_lazy('inventory:list_term')) , name="delete_term" )


]
