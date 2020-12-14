from django.contrib import admin
from .models import Result
from django.utils.safestring import mark_safe

class ResultAdmin(admin.ModelAdmin):
    list_display = ['id' ,  'description', 'name', 'uploaded_file' , 'get_share']
    list_display_links = ['id' , 'description']
    list_editable = ['uploaded_file' ]

    def get_share(self , obj):
        return mark_safe(f'<a href="http://127.0.0.1:8000/result/query/{obj.share}" target="_blank"> \
        http://127.0.0.1:8000/result/query/{obj.share}</a>')

    get_share.short_description = "Shareable Link"

# Register your models here.
admin.site.register(Result , ResultAdmin)