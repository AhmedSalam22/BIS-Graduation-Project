from django.contrib import admin
from .models import Journal , Accounts



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
    list_display = ('account' , 'date' , 'balance' , 'transaction_type' , 'comment' , 'owner')
    list_editable = ['comment']
    search_fields = ['comment']
    list_filter = ['account', 'transaction_type' , 'owner']
    sortable_by = ['account' ,'date' ,'balance' , 'date' , 'transaction_type' ,  'owner']
    ordering = ['-date' , 'owner']
    # fields = ('owner' , ('account' , 'date' , 'balance' , 'transaction_type' ) , 'comment')

    fieldsets = (
        ("Main", {
            "fields": ['owner' , ('account' , 'date' , 'balance' , 'transaction_type' )],
        }),
        ("optional" , {
            "fields": ["comment"],
            "classes": ('collapse',)
        }
        )
    )
    

    actions_on_bottom = True

# Register your models here.
admin.site.register(Accounts , AccountsAdmin)
admin.site.register(Journal , JournalAdmin)

# Customize Django Admin
admin.site.site_header = "AYBA -Automate Your Business Activity- by Ahmed Maher"
admin.site.site_title = "AYBA"
admin.site.index_title = "Dashboard"