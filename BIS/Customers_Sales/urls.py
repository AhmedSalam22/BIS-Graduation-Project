from django.urls import path , include
from . import views
from django.views.decorators.cache import cache_page

app_name = "Customer_Sales"
urlpatterns = [
    path('add_customer' , views.CoustomerView.as_view() ),
    path('', cache_page(60 * 60)(views.Home.as_view()), name='home')
]
