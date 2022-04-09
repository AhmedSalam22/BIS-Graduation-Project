import django_filters
from suppliers.models import Supplier

class SupplierFilter(django_filters.FilterSet):

    class Meta:
        model = Supplier
        fields = {
                'name': ['icontains'],
                }