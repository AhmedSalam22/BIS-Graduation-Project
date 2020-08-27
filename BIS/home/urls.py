from django.urls import path , include
from django.views.generic import TemplateView
from . import views

app_name = "home"
urlpatterns = [
    path("" , TemplateView.as_view(template_name = "home/index.html") , name="home") , 
    path('accounts/', include('django.contrib.auth.urls')),
    path('register' , views.Register.as_view() , name="register")
]
