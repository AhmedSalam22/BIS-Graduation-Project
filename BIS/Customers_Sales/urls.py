from django.urls import path , include
from . import views

app_name = "Customer_Sales"
urlpatterns = [
    path('add_customer' , views.CoustomerView.as_view() ),
    path('', views.Home.as_view(), name='home')
]
