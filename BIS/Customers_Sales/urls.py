from django.urls import path , include
from . import views

app_name = "Customer_Sales"
urlpatterns = [
    path('' , views.CoustomerView.as_view() )
]
