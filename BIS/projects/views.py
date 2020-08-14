from django.shortcuts import render
from django.views.generic import ListView
from .models import Projects
# Create your views here.

class ProjectsListView(ListView):
    model = Projects
    template_name = 'projects/index.html'
