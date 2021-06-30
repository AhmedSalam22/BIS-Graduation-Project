import django_filters
from inventory.models import Inventory



class InventoryFilter(django_filters.FilterSet):
    class Meta:
        model = Inventory
        fields = {'item_name': ['icontains'], 'description': ['icontains']}