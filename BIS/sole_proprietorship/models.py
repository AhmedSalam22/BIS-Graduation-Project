from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.
class Accounts(models.Model):
    class Meta:
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
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
    comment = models.CharField(max_length=1500 , null= True , blank=True )

    def __str__(self):
        return f"{self.account}"


class ReportingPeriodConfig(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name= "fs_reporting_period",
    )
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.owner}: from {self.start_date} to {self.end_date}"
    