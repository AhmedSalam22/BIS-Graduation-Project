from django.contrib import admin
from .models import Journal , Accounts
# Register your models here.
admin.site.register([Journal , Accounts])


admin.site.site_header = "AYBA -Automate Your Business Activity- by Ahmed Maher"
admin.site.site_title = "AYBA"
admin.site.index_title = "Dashboard"