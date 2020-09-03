from django.shortcuts import render , get_object_or_404
from django.http import HttpResponse
from .models import Result
import pandas as pd

# Create your views here.
def result_query(request , share):
    obj = get_object_or_404(Result , share=share)
    df = pd.read_csv(obj.uploaded_file)
    query = request.GET.get('query')
    result = df.query('account_id == @query')

    ctx = {
        'result': result.to_html()
    }
    return render(request , 'result/query.html' , ctx)
