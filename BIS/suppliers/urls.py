from django.urls import path, reverse_lazy
from . import views
from django.views.decorators.cache import cache_page

app_name='suppliers'
urlpatterns = [
   path('create_supplier', views.CreateSupplierView.as_view(success_url=reverse_lazy('inventory:home')), name='create_supplier'),

]

# We use reverse_lazy in urls.py to delay looking up the view until all the paths are defined
