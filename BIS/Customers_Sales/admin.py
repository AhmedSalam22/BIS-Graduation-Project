from django.contrib import admin
from .models import Customer , CustomerEmail , CustomerAddress , CustomerNote


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
    list_display = ['first_name' , 'middle_name' , 'last_name']
    # list_filter = ['' , 'prospect' , 'inactive']
    search_fields =['first_name' , 'middle_name' , 'last_name']
    inlines = [CustomerAddressInline , CustomerEmailInline]

    save_on_top = True

    fieldsets = (
        ("Main", {
            "fields": [
                'owner' ,('first_name' , 'middle_name' , 'last_name' ), 
            ],
        }),
        # ('Optionl', {
        #     "fields" : ['prospect' , 'inactive'] ,
        #     "classes" : ('collapse',)
        # }),
    )
    


# Register your models here.

admin.site.register(Customer , CustomerAdmin)
admin.site.register([
 CustomerEmail , 
 CustomerAddress , 
 CustomerNote])