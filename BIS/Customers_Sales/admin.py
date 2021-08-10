from django.contrib import admin
from .models import Customer , CustomerEmail  , CustomerType , CustomerAddress , CustomerNote


class CustomerAddressInline(admin.TabularInline):
    model = CustomerAddress
    show_change_link = True

    def get_extra(self , request , obj=None , **kwargs):
        if obj:
            return 1
        return 3

    

class CustomerEmailInline(admin.TabularInline):
    model = CustomerEmail
    
    def get_extra(self , request , obj=None , **kwargs):
        if obj:
            return 1
        return 3



class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name' , 'middle_name' , 'last_name' , 'account_number' , 'customer_type']
    list_filter = ['customer_type' , 'prospect' , 'inactive']
    search_fields =['first_name' , 'middle_name' , 'last_name' , 'account_number']
    inlines = [CustomerAddressInline , CustomerEmailInline]

    save_on_top = True

    fieldsets = (
        ("Main", {
            "fields": [
                'owner' ,('first_name' , 'middle_name' , 'last_name' ), 'customer_type'
            ],
        }),
        ('Optionl', {
            "fields" : ['prospect' , 'inactive'] ,
            "classes" : ('collapse',)
        }),
    )
    


# Register your models here.

admin.site.register(Customer , CustomerAdmin)
admin.site.register([
 CustomerEmail , 
 CustomerType , 
 CustomerAddress , 
 CustomerNote])