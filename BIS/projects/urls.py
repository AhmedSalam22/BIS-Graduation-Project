from django.urls import path 
from .views import ProjectsListView , ProjectsDetailView
app_name = "projects"
urlpatterns = [
    path("" , ProjectsListView.as_view(), name="home"), 
    path("/<int:pk>" , ProjectsDetailView.as_view() , name="detail")
]
