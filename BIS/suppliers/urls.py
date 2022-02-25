from django.urls import path, reverse_lazy
from . import views
from django.views.decorators.cache import cache_page

app_name='suppliers'
urlpatterns = [
   path('create_supplier', views.CreateSupplierView.as_view(success_url=reverse_lazy('suppliers:supplier_list')), name='create_supplier'),
   path('supplier_list', views.SupplierListView.as_view(), name='supplier_list'),
   path('supplier_delete/<int:pk>', views.SupplierDeleteView.as_view(success_url=reverse_lazy('suppliers:supplier_list')), name='supplier_delete'),
   path('update_supplier/<int:pk>', views.SupplierUpdateView.as_view(success_url=reverse_lazy('suppliers:supplier_list')), name='supplier_update'),
]

# We use reverse_lazy in urls.py to delay looking up the view until all the paths are defined
