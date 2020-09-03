from django.urls import path 
from . import views

app_name = "result"
urlpatterns = [
    path("query/<slug:share>" , views.result_query )
]
