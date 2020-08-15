from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.
class Accounts(models.Model):
    # account , Type , Normal Balance 
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.CharField(max_length = 250)
    normal_balance = models.CharField(
        max_length=7,
        choices= [ 
            ("Debit" , "Debit") , 
            ("Credit" , "Credit")
        ],
        default= "Debit",
    )
    account_type = models.CharField(
        max_length = 50, 
        choices = [
            ("Assest" , "Assest"),
            ("Investment" , "Investment"),
            ("liabilities" , "liabilities"),
            ("Revenue" , "Revenue"),
            ("Expenses" , "Expenses"),
            ("Drawings", "Drawings")
  
        ] , 
        default = "Assest"
    )

    def __str__(self):
        return self.account

class Journal(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    account = models.ForeignKey(Accounts, on_delete=models.CASCADE)

    date = models.DateField()
    balance = models.FloatField()
    transaction_type = models.CharField(
        max_length=7,
        choices= [ 
            ("Debit" , "Debit") , 
            ("Credit" , "Credit")
        ],
        default= "Debit",
    )
    comment = models.CharField(max_length=1500)

    def __str__(self):
        return self.account