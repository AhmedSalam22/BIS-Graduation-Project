from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.
class Supplier(models.Model):
    """
    Create Supplier Table in db.
    """
    owner = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    first_name  = models.CharField(max_length=50)
    last_name   = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50 , blank=True , null=True)

    @property
    def full_name(self):
        """Returns the customer's full name."""
        return '%s %s %s' % (self.first_name, self.middle_name , self.last_name)

    def __str__(self):
        return self.full_name