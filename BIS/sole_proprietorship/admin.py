from django.contrib import admin
from .models import Journal , Accounts , ReportingPeriodConfig, Transaction



class JournalInline(admin.TabularInline):
    model = Journal

class AccountsAdmin(admin.ModelAdmin):
    list_display = ( 'account' , 'normal_balance' , 'account_type' , 'get_owner' )
    list_editable = ('normal_balance' , 'account_type')
    list_filter = ['normal_balance' , 'account_type' , 'owner']
    fields = ( 'owner' , ('account' , 'normal_balance' , 'account_type' ))
    inlines = [JournalInline]

    def get_owner(self , rec):
        return rec.owner.username

  

    get_owner.short_description = "Owner"
    actions_on_bottom = True


class JournalAdmin(admin.ModelAdmin):
    list_display = ('account' ,  'balance' , 'transaction_type' ,  )

    list_filter = ['account', 'transaction_type']
    sortable_by = ['account' ,'balance' , 'transaction_type' , ]
    # fields = ('owner' , ('account' , 'date' , 'balance' , 'transaction_type' ) , 'comment')

    fieldsets = (
        ("Main", {
            "fields": [ ('account' , 'balance' , 'transaction_type' )],
        }),
        # ("optional" , {
        #     "fields": ["comment"],
        #     "classes": ('collapse',)
        # }
        # )
    )
    

    actions_on_bottom = True

class ReportingPeriodConfigAdmin(admin.ModelAdmin):
    list_display = ['owner' , 'start_date' , 'end_date']
    list_editable = ['start_date' , 'end_date']
    fields = ('owner' , ( 'start_date', 'end_date'))



# Register your models here.
admin.site.register(Accounts , AccountsAdmin)
admin.site.register(Transaction)
admin.site.register(Journal , JournalAdmin)
admin.site.register(ReportingPeriodConfig , ReportingPeriodConfigAdmin)
# Customize Django Admin
admin.site.site_header = "AYBA -Automate Your Business Activity- by Ahmed Maher"
admin.site.site_title = "AYBA"
admin.site.index_title = "Dashboard"