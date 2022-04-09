from django.db import models
from django.conf import settings
# from phonenumber_field.modelfields import PhoneNumberField 
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from ckeditor.fields import RichTextField
from home.constant import ISO_3166_CODES

# Create your models here.
class Customer(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name  = models.CharField(max_length=50)
    last_name   = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50 , blank=True , null=True)

    name = models.CharField(max_length=150)

    @property
    def full_name(self):
        """Returns the customer's full name."""
        return f'{self.first_name} {self.middle_name if self.middle_name != None else ""} {self.last_name}'


    def save(self, *args, **kwargs):
            self.name = f'{self.first_name} {self.middle_name} {self.last_name}'
            super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name

class CustomerCommonFields(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    class Meta:
        abstract = True



class CustomerEmail(CustomerCommonFields):
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.email

# class Telephone (CustomerCommonFields):
#     phone_number = PhoneNumberField(blank=True , region="EG")

#     def __str__(self):
#         return f"{self.phone_number}"



def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'customer_sales/cutomer_imgs/user_{0}/{2}{1}'.format(instance.owner.id, filename , timezone.now())

class CustomerImage(CustomerCommonFields):
    image = models.ImageField(upload_to=user_directory_path,
                                null=True,
                                blank=True,
                                editable=True,
                                help_text="Customer Picture",
                             )
    
    def __str__(self):
        return f"img:{self.customer.first_name} {self.customer.middle_name} {self.customer.last_name}"

    
class CustomerAddress(CustomerCommonFields):
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
        return f"{self.customer.first_name} {self.customer.middle_name} {self.customer.last_name}:{self.address1}"

        

class CustomerNote(CustomerCommonFields):
    note = RichTextField(blank=True , null=True)

    def __str__(self):
        return f"note:{self.customer.first_name} {self.customer.middle_name} {self.customer.last_name}"


class CustomerPhone(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    phone =  models.CharField(max_length = 16, blank=True, null=True)

    def __str__(self):
        return f'{self.phone}'
