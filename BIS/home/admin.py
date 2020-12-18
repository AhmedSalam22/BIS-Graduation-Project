from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User , Group


class MyAdminSite(admin.AdminSite):

    def get_urls(self):
        urlpatterns = super().get_urls()
        urlpatterns += [

        ] 

        return urlpatterns


admin.site = MyAdminSite()
admin.site.register(User, UserAdmin)
admin.site.register(Group , GroupAdmin)