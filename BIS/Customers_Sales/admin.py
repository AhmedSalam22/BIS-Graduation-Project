from django.contrib import admin
from .models import Customer , CustomerEmail , Telephone , CustomerType , CustomerAddress , CustomerNote
# Register your models here.
admin.site.register([Customer ,
 CustomerEmail , 
 Telephone , 
 CustomerType , 
 CustomerAddress , 
 CustomerNote])