from inventory.models import PaymentSalesTerm
class Helper:

    @staticmethod
    def cash_or_accounts_payable(purchase_invoice):
        """
        Determine whether use cash or A/P when journalize
        """
        if purchase_invoice.term.terms == PaymentSalesTerm.Term.CASH.value:
            return purchase_invoice.term.cash_account
        else:
            return purchase_invoice.term.accounts_payable