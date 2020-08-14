from django.urls import path 
from .views import ProjectsListView
app_name = "projects"
urlpatterns = [
    path("" , ProjectsListView.as_view())
]
