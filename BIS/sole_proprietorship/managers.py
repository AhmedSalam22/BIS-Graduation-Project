from django.db import models, connection
import pandas as pd

class FinancialAnalysis(models.Manager):
    SQL = """
            SELECT   account_type , account, classification, sum(helper) as balance, sum(current_period) as current_period,
                sum(previous_period) as previous_period
                FROM (
                    SELECT 
                            a.classification,
                            a.account_type , a.account  , a.normal_balance ,
                            t.date,
                            CASE
                                WHEN j.transaction_type = a.normal_balance Then  j.balance
                                ELSE ( -1 * j.balance)
                            END as helper,
                            CASE
                                WHEN t.date >= %s AND  j.transaction_type = a.normal_balance Then  j.balance
                                WHEN t.date >= %s  AND j.transaction_type <> a.normal_balance Then  ( -1 * j.balance)
                            END as current_period,
                            CASE
                                WHEN t.date < %s AND  j.transaction_type = a.normal_balance Then  j.balance
                                WHEN t.date < %s  AND j.transaction_type <> a.normal_balance Then  ( -1 * j.balance)
                            END as previous_period
                        FROM sole_proprietorship_journal as j
                        JOIN sole_proprietorship_accounts as a
                        on j.account_id = a.id
                        JOIN sole_proprietorship_transaction as t
                        ON j.transaction_id = t.id
                        where a.owner_id = %s  AND t.date <= %s ) as temp_table
                GROUP by account_type , account, classification
                ORDER by balance DESC
    """

    def data_frame(self, owner):
        with connection.cursor() as cursor:
            cursor.execute(self.SQL, [
                owner.fs_reporting_period.start_date,
                owner.fs_reporting_period.start_date,
                owner.fs_reporting_period.start_date,
                owner.fs_reporting_period.start_date,
                owner.id,
                owner.fs_reporting_period.end_date
            ])
            df = pd.DataFrame(cursor.fetchall() , columns=['account_type',	'account',	'classification',	'balance',	'current_period',	'previous_period'])
        return df

    def analysis(self, owner):
        data = {}
        df = self.data_frame(owner)

        net_sales = df.query('classification == "Sales"')['balance'].sum() - df.query('classification == "Revenue-Contra"')['balance'].sum()
        gross_profit = net_sales - df.query('classification == "COGS"')['balance'].sum()
        operating_income = gross_profit - df.query('classification == "Operating Expense"')['balance'].sum()
        net_income = operating_income + df.query('classification == "Other Revenue and gains"')['balance'].sum() - df.query('classification == "Other Expenses And Losses"')['balance'].sum()
        avg_total_assets = (df.query('account_type == "Assest"')['previous_period'].sum() + df.query('account_type == "Assest"')['balance'].sum()) / 2
        beg_equity = (
            df.query('account_type == "Investment"')['previous_period'].sum()  +
            df.query('account_type == "Revenue"')['previous_period'].sum()  -
            df.query('account_type == "Expenses"')['previous_period'].sum() -
            df.query('account_type == "Drawings"')['previous_period'].sum()
        )

        end_equity = (
            df.query('account_type == "Investment"')['balance'].sum()  +
            df.query('account_type == "Revenue"')['balance'].sum()  -
            df.query('account_type == "Expenses"')['balance'].sum() -
            df.query('account_type == "Drawings"')['balance'].sum()
        )
        
        avg_total_equity = (beg_equity + end_equity) / 2
        current_assets_q = """
        classification == "Current Assets" or classification == "Cash" or classification == "Marketable securities or short-term investments" \
        or classification == "Receivable" or classification == "Inventory" or classification == "prepaids"
        """
        current_assets = df.query(current_assets_q)['balance'].sum()
        current_liability = df.query('classification == "Current liabilities" ')['balance'].sum()

        avg_inventory = (df.query('classification == "Inventory"')['previous_period'].sum() + df.query('classification == "Inventory"')['balance'].sum()) / 2

        avg_gross_receivables = (
            (df.query('classification == "Receivable"')['previous_period'].sum() -  df.query('classification == "Allowance for Doubtful Accounts"')['previous_period'].sum() ) /
            + (df.query('classification == "Receivable"')['balance'].sum() -  df.query('classification == "Allowance for Doubtful Accounts"')['balance'].sum() ) 
        ) / 2

        #profitability analysis
        data['net_profit_margin'] = ( net_income / net_sales ) if net_sales != 0 else 0
        data['gross_profit_margin'] = ( gross_profit / net_sales ) if net_sales != 0 else 0
        data['total_assets_turnover'] = ( net_sales / avg_total_assets ) if avg_total_assets != 0 else 0
        data['rate_of_return_on_assets'] = ( net_income / avg_total_assets ) if avg_total_assets != 0 else 0
        data['rate_of_return_on_total_equity'] = ( net_income / avg_total_equity ) if avg_total_equity != 0 else 0
        
        #convert data into percentages %
        for key, value in data.items():
            data[key] = round(value * 100, 2)
            
        #liquidiy analysis
        data['current_ratio'] =  ( current_assets / current_liability ) if current_liability != 0 else 0
        data['acid_test_ratio'] = (
            df.query('classification == "Cash" or classification == "Marketable securities or short-term investments" or classification == "Receivable"')['balance'].sum() /
            current_liability
            ) if current_liability != 0 else 0
        data['quick_ratio'] = (
            (current_assets - (df.query('classification == "Inventory" or classification == "prepaids"')['balance'].sum())) / current_liability
            ) if current_liability != 0 else 0

        data['cash_ratio'] = (
            df.query('classification == "Cash" or classification == "Marketable securities or short-term investments" ')['balance'].sum() /
            current_liability
            ) if current_liability != 0 else 0

        
        #operating cycle
        data['inventory_turnover_in_times'] =  (df.query('classification == "COGS"')['balance'].sum() / avg_inventory ) if avg_inventory != 0 else 0
        data['inventory_turnover_in_days'] = (365 / data['inventory_turnover_in_times']) if data['inventory_turnover_in_times'] != 0 else 0
        data['acc_rec_turnover_in_times'] = ( net_sales / avg_gross_receivables ) if avg_gross_receivables != 0 else 0
        data['acc_rec_turnover_in_days'] = ( 365 / data['acc_rec_turnover_in_times'] ) if data['acc_rec_turnover_in_times'] != 0 else 0
        data['operating_cycle'] = data['acc_rec_turnover_in_days']  + data['inventory_turnover_in_days']

        return data

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
                    ORDER BY t.date, t.id

                                                """ , [owner_id, account, start_date, end_date])
            data = cursor.fetchall()
        return data

    def account_over_time(self, owner_id, account, start_date, end_date):
        """
        Return the dataset for a specific account over the time
        """
        with connection.cursor() as cursor:
            cursor.execute(""" 
                SELECT t.date,
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
            data = cursor.fetchall()
        return data

    def accounts_type_balances(self, owner_id, end_date):
        """
            return [(balance, account_types) ....]
        """
        with connection.cursor() as cursor:
            cursor.execute(""" 
                            SELECT sum(helper) as balance,  account_type FROM (
                                                    SELECT * ,
                                                    CASE
                                                        WHEN j.transaction_type = a.normal_balance Then  j.balance
                                                        ELSE ( -1 * j.balance)
                                                    END as helper 
                                                    FROM sole_proprietorship_journal as j
                                                    JOIN sole_proprietorship_accounts as a
                                                    on j.account_id = a.id
                                                    JOIN sole_proprietorship_transaction as t
                                                    ON j.transaction_id = t.id
                                                    where a.owner_id = %s  AND t.date <= %s )  as temp_table
            GROUP by account_type
            ORDER by balance DESC
                                                    """ , [owner_id, end_date])
            data = list(cursor)
        return data


    def account_type_account_balance(self, owner_id, account_type, end_date):      
        """
            return [(account_type, account, balance) ....]
        """
        with connection.cursor() as cursor:
            cursor.execute(""" 
                SELECT account_type, account, 
                        SUM(CASE
                            WHEN j.transaction_type = a.normal_balance Then  j.balance
                            ELSE ( -1 * j.balance)
                        END) as balance 
                        FROM sole_proprietorship_journal as j
                        JOIN sole_proprietorship_accounts as a
                        on j.account_id = a.id
                        JOIN sole_proprietorship_transaction as t
                        ON j.transaction_id = t.id
                        where a.owner_id = %s  AND t.date <= %s and a.account_type = %s 
                    GROUP BY account_type, account
                    ORDER BY balance 
                                                    """ , [owner_id, end_date, account_type])
            data = cursor.fetchall()
        return data

    def cash_flow(self, owner):
        with connection.cursor() as cursor:
            cursor.execute(""" 
               SELECT 
                    CASE
                        WHEN j.transaction_type = a.normal_balance Then 'Cash Inflow'
                        ELSE ('Cash Outflow')
                    END as cash_flow,
                    to_char(t.date, 'yyyy-Month') as "year_month",
                    to_char(t.date, 'mm')::integer as "month_num",
                    SUM(j.balance)as balance
                FROM sole_proprietorship_journal as j
                JOIN sole_proprietorship_accounts as a
                on j.account_id = a.id
                JOIN sole_proprietorship_transaction as t
                ON j.transaction_id = t.id
                where  a.owner_id = %s  AND t.date >= %s AND t.date <= %s   and a.classification = 'Cash'
                GROUP BY   cash_flow, "month_num", "year_month"
                ORDER BY "month_num"
                                                    """ , [owner.id,
                                                            owner.fs_reporting_period.start_date,
                                                            owner.fs_reporting_period.end_date])
            df = pd.DataFrame(cursor.fetchall(), columns=['cash_flow', 'year_month','month_num', 'balance'])
        return df

class TransactionManager(models.Manager):
    def total_debit_and_total_credit(self, owner_id, end_date=None):
        """
        return {
            'Debit': amount(float)
            'Credit: amount(float)
        }
        """
        result = dict()
        with connection.cursor() as cursor:
            if end_date == None or end_date =='':
                cursor.execute("""
                    SELECT MAX(date) FROM sole_proprietorship_transaction as t
                    JOIN sole_proprietorship_journal as j
                    ON j.transaction_id = t.id
                    JOIN sole_proprietorship_accounts as a
                    ON j.account_id = a.id
                    WHERE a.owner_id = %s
                """,  [owner_id])
                end_date = cursor.fetchone()[0]


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
                            where a.owner_id = %s and t.date <= %s
                                        ) as temp_table
                    GROUP by normal_balance 

                                                    """ , [owner_id, end_date])
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