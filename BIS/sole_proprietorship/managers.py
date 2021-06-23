from django.db import models, connection

class AccountManager(models.Manager):
    def beginning_balance(self, owner_id, end_date, account):
        """
        Return the beginning balance for the given period 
        (Ending balance will be beggning balance for the next period)
        """
        with connection.cursor() as cursor:
            cursor.execute(""" 
                SELECT 
                    sum(CASE
                        WHEN j.transaction_type = a.normal_balance Then  j.balance
                        ELSE ( -1 * j.balance)
                    END ) as beg_balance
                    FROM sole_proprietorship_accounts as a
                    JOIN sole_proprietorship_journal as j
                    ON j.account_id = a.id
                    JOIN sole_proprietorship_transaction as t
                    ON t.id = j.transaction_id
                    WHERE a.owner_id = %s  and a.id = %s and t.date < %s
                                                """ , [owner_id, account, end_date])
            beg_balacne = cursor.fetchone()
            print(f'beg_balacne: {beg_balacne}, end_date={end_date} account_id={account} owner_id= {owner_id}')

        return beg_balacne[0] if beg_balacne[0] != None else 0


    def ledger(self, owner_id, account, start_date, end_date):
        """
        Return the dataset for a specific account to use it in General Ledger
        """
        print('ledger is invoked')
        with connection.cursor() as cursor:
            cursor.execute(""" 
                SELECT t.date, t.comment, j.transaction_type,
                    (CASE
                        WHEN j.transaction_type = a.normal_balance Then  j.balance
                        ELSE ( -1 * j.balance)
                    END )as amount
                    FROM sole_proprietorship_accounts as a
                    JOIN sole_proprietorship_journal as j
                    ON j.account_id = a.id
                    JOIN sole_proprietorship_transaction as t
                    ON t.id = j.transaction_id
                    
                    WHERE a.owner_id = %s  and a.id = %s and t.date >= %s and t.date <= %s
                    ORDER BY t.date

                                                """ , [owner_id, account, start_date, end_date])
            print('done')
            data = cursor.fetchall()
            print(f'start_date: {start_date}, end_date={end_date} account_id={account} owner_id= {owner_id}')
            print(data)
        return data







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