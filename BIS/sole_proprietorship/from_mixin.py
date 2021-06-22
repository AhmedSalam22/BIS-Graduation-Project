from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class TransactionValidation:
    def clean(self):
        """Checks that total debit is equal to total credit"""
        super().clean()
        totalDebit = 0.0
        totalCredit = 0.0
        for form in self.forms:
            transaction_type = form.cleaned_data.get('transaction_type')
            if transaction_type == "Debit":
                totalDebit += form.cleaned_data.get('balance', 0)
            else:
                totalCredit += form.cleaned_data.get('balance', 0)

     

        
        if totalDebit != totalCredit:
            raise ValidationError(_(f"Total Debit ={totalDebit} is not equal to Toal Credit = {totalCredit}"))
