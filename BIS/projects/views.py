from django.shortcuts import render
from django.views.generic import ListView , DetailView
from .models import Projects
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Q
from django.views import View
from django.http import  HttpResponse
from django.core.serializers import serialize

# Create your views here.

class ProjectsListView(ListView):
    model = Projects
    template_name = 'projects/index.html'

class ProjectsDetailView(DetailView):
    model = Projects
    template_name = 'projects/detail.html'


class ProjectsListViewAjax(View):
    def get(self, request , search) :
        if search !="None" :
            # Multi-field search
            query = Q(title__contains=search)
            query.add(Q(detail__contains=search), Q.OR)
            query.add(Q(tag__contains=search), Q.OR)
            objects = Projects.objects.filter(query).select_related()
        else :
            objects = Projects.objects.all()

        data = serialize('json', objects)
        return HttpResponse(data, content_type="application/json")

