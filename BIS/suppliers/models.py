from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.functions import Concat
from django.db.models import Value, F
from home.constant import ISO_3166_CODES
from ckeditor.fields import RichTextField


class SupplierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            supplier_full_name = Concat(F('first_name'), Value(' '), F('middle_name'), Value(' '), F('last_name'))
        )


class Supplier(models.Model):
    """
    Create Supplier Table in db.
    """
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    first_name  = models.CharField(max_length=50)
    last_name   = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50 , blank=True , null=False , default=" ")
    name = models.CharField(max_length=150)


    objects = SupplierManager()
    
    @property
    def full_name(self):
        """Returns the customer's full name."""
        return '%s %s %s' % (self.first_name, self.middle_name , self.last_name)


    def save(self, *args, **kwargs):
        self.name = f'{self.first_name} {self.middle_name} {self.last_name}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.full_name}'

class SupplierEmail(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f'{self.email}'

class SupplierPhone(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    phone =  models.CharField(max_length = 16, blank=True, null=True)

    def __str__(self):
        return f'{self.phone}'



class SupplierAddress(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    address1 = models.CharField(
        "Address line 1",
        max_length=1024,
        blank=True ,
        null=True
    )


    address2 = models.CharField(
        "Address line 2",
        max_length=1024,
        null = True,
        blank= True
    )

    zip_code = models.CharField(
        "ZIP / Postal code",
        max_length=12,
        blank=True ,
        null=True
    )

    city = models.CharField(
        "City",
        max_length=1024,
        blank=True ,
        null=True
    )

    country = models.CharField(
        "Country",
        max_length=3,
        choices=ISO_3166_CODES,
        blank=True ,
        null=True
    )

    def __str__(self):
        return f"{self.address1}, {self.address2}, {self.zip_code}, {self.city}, {self.country}"

        

class SupplierNote(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    note = RichTextField(blank=True , null=True)

    def __str__(self):
        return f"note:{self.note}"




