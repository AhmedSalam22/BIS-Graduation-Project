from django.db import models, connection

class TransactionManager(models.Manager):
    def total_debit_and_total_credit(self, owner_id):
        """
        return {
            'Debit': amount(float)
            'Credit: amount(float)
        }
        """
        result = dict()
        with connection.cursor() as cursor:
            cursor.execute(""" 
                   SELECT   sum(helper) as balance ,  normal_balance  FROM (
                        SELECT normal_balance,
                            CASE
                                WHEN j.transaction_type = a.normal_balance Then  j.balance
                                ELSE ( -1 * j.balance)
                            END as helper 
                            FROM sole_proprietorship_journal as j
                            JOIN sole_proprietorship_accounts as a
                            on j.account_id = a.id
                            JOIN sole_proprietorship_transaction as t
                            ON j.transaction_id = t.id
                            where t.owner_id = %s
                                        )
                    GROUP by normal_balance 

                                                    """ , [owner_id])
            row = list(cursor.fetchall())
        try:
            result["Credit"] = row[0][0]
        except IndexError:
            result["Credit"] = 0

        try:
            result["Debit"] = row[1][0]
        except IndexError:
            result["Debit"] = 0

        return result