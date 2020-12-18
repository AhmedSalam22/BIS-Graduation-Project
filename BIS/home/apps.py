from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig

class HomeConfig(AppConfig):
    name = 'home'

class MyAdminConfig(AdminConfig):
    default_site = "home.admin.MyAdminSite"
