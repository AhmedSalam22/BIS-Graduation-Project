from django.shortcuts import render , get_object_or_404
from django.http import HttpResponse
from .models import Result
import pandas as pd

# Create your views here.
def result_query(request , share):
    obj = get_object_or_404(Result , share=share)
    query = request.GET.get('query' , None) 
    try:
        query = int(query)
    except:
        query = None

    try:
        df = pd.read_csv(obj.uploaded_file , sep=";")
        result = df[df[obj.name] == query]
    except:
        df = pd.read_csv(obj.uploaded_file , sep=",")
        result = df[df[obj.name] == query]

    ctx = {
        'result': result.T.to_html(classes = "table table-hover table-borderless")
    }
    return render(request , 'result/query.html' , ctx)
