from django.db import models
from ckeditor.fields import RichTextField

# Create your models here.
class Projects(models.Model):
    title = models.CharField(max_length=50)
    summary = models.CharField(max_length=250)
    detail = RichTextField()
    release_date = models.DateField()
    tag = models.CharField(max_length=50)
    img = models.ImageField(upload_to="media/projects" , blank = True)


    def __str__(self):
        return self.title