from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout , Row , Column , Submit , Div
from crispy_forms.bootstrap import TabHolder, Tab

# Row(Column('purchase_date__gte', 'purchase_date__lte', 'due_date__gte', 'due_date__lte'), 
#                     Column('status', 'term'),
#                 ),

class PurchaseFilterHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
           Div(
               TabHolder(
                    Tab('Date',
                        Row(
                            Column('purchase_date__gte', 'purchase_date__lte'),
                            Column('due_date__gte', 'due_date__lte')
                        )
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
                        Row(
                            Column('num_returend__gte', 'num_returend__lte'),
                            Column('cost_returned__gte', "cost_returned__lte"),
                            Column('total_purchases__gte', 'total_purchases__lte'),
                            Column('net_purchases__gte', 'net_purchases__lte'),
                            Column('total_amount_paid__gte', 'total_amount_paid__lte')
                        )
                    )
                )
            )
        )
        self.form_tag = False