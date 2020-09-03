from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
# Create your models here.

def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'results/user_{0}/{1}'.format(instance.owner.id, filename)

class Result(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length = 250)
    description = models.TextField(max_length=1000) 
    uploaded_file = models.FileField(upload_to=user_directory_path ,
                                     max_length=100 , 
                                     help_text= 'Upload your File in csv format and less than 100 megabyte ' , 
                                     validators= [FileExtensionValidator(allowed_extensions=['csv'])] , 
                                     blank=False , 
                                     null=False , 
                                     editable = True
                                     )
    share = models.CharField(max_length=500 ,unique=True , blank=False , null=False )


    def __str__(self):
        return self.name

@receiver(post_delete, sender=Result)
def submission_delete(sender, instance, **kwargs):
    instance.uploaded_file.delete(False) 