from django.urls import path, reverse_lazy
from . import views
from django.views.decorators.cache import cache_page

app_name='suppliers'
urlpatterns = [
   path('create_supplier', views.CreateSupplierView.as_view(success_url=reverse_lazy('suppliers:supplier_list')), name='create_supplier'),
   path('supplier_list', views.SupplierListView.as_view(), name='supplier_list'),
   path('supplier_delete/<int:pk>', views.SupplierDeleteView.as_view(success_url=reverse_lazy('suppliers:supplier_list')), name='supplier_delete'),
   path('update_supplier/<int:pk>', views.SupplierUpdateView.as_view(success_url=reverse_lazy('suppliers:supplier_list')), name='supplier_update'),
   path('supplier_detail/<int:pk>', views.SupplierDetailView.as_view(), name="supplier_detail"),
   path('add_phone/<int:supplier_id>', views.AddPhoneView.as_view(), name='add_phone'),
   path('add_email/<int:supplier_id>', views.AddEmailView.as_view(), name='add_email'),
   path('add_address/<int:supplier_id>', views.AddAddressView.as_view(), name='add_address'),
   path('add_note/<int:supplier_id>', views.AddNoteView.as_view(), name='add_note'),
   path('update_phone/supplier/<int:supplier_pk>/phone/<int:pk>', views.SupplierPhoneUpdateView.as_view(), name='update_phone'),
   path('update_adress/supplier/<int:supplier_pk>/address/<int:pk>', views.SupplierAddressUpdateView.as_view(), name='update_address'),
   path('update_email/supplier/<int:supplier_pk>/email/<int:pk>', views.SupplierEmailUpdateView.as_view(), name='update_email'),
   path('update_note/supplier/<int:supplier_pk>/note/<int:pk>', views.SupplierNoteUpdateView.as_view(), name='update_note'),
   path('delete_phone/supplier/<int:supplier_pk>/phone/<int:pk>', views.SupplierPhoneDeleteView.as_view(), name='delete_phone'),
   path('delete_email/supplier/<int:supplier_pk>/email/<int:pk>', views.SupplierEmailDeleteView.as_view(), name='delete_email'),
   path('delete_address/supplier/<int:supplier_pk>/address/<int:pk>', views.SupplierAddressDeleteView.as_view(), name='delete_address'),
   path('delete_note/supplier/<int:supplier_pk>/note/<int:pk>', views.SupplierNoteDeleteView.as_view(), name='delete_note'),


   
]

# We use reverse_lazy in urls.py to delay looking up the view until all the paths are defined
