from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout , Row , Column , Submit , Div
from crispy_forms.bootstrap import TabHolder, Tab



class InventoryFilterHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
            Row(
                Column('item_name__icontains'), Column('description__icontains')
            )
        )
        self.form_tag = False


class PurchaseFilterHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
           Div(
               TabHolder(
                    Tab('Date',
                        Row('purchase_date__gte'),
                        Row('purchase_date__lte'),
                        Row('due_date__gte'),
                        Row('due_date__lte')
                    ),
                    Tab('dropdown',
                        Row(
                             Column('supplier')
                        ),
                        Row(
                            Column('status'), Column('term')
                        )
                    ),
                    Tab(
                        'other',
                        
                            Row('num_returend__gte', 'num_returend__lte'),
                            Row('cost_returned__gte', "cost_returned__lte"),
                            Row('total_purchases__gte', 'total_purchases__lte'),
                            Row('net_purchases__gte', 'net_purchases__lte'),
                            Row('total_amount_paid__gte', 'total_amount_paid__lte')
                        
                    )
                )
            )
        )
        self.form_tag = False
        self.disable_csrf = True


class SalesFormsetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout( 
            Div(Row(Column('item') , Column('sale_price') , Column('quantity') ) , css_class="link-formset" )
        )
        self.form_tag = False


                                     
class SalesAllowanceFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
           Div(
                Row(Column('date'), Column('amount', 'DELETE') ),
           )
        )
        self.render_required_fields = True
        self.form_tag = False