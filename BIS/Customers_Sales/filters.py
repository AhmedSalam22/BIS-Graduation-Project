import django_filters
from .models import Customer

class CustomerFilter(django_filters.FilterSet):

    class Meta:
        model = Customer
        fields = {
                'name': ['icontains'],
                }