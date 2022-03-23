from django.utils import timezone
from django import forms
from typing import List
from django.template.loader import get_template
from io import BytesIO
from xhtml2pdf import pisa
from django.http import HttpResponse
import os
from django.conf import settings
from django.contrib.staticfiles import finders

class DateInput(forms.DateInput):
    input_type = 'date'
    
class DateField:
    def __init__(self, field: str, initial: bool = False)  -> None:
        self.field = field
        self.initial = initial


class DateMixin:
    def date(self, date_fields: List[DateField], django_filter=False) -> None:
        if not django_filter:
            for date_field in date_fields:
                self.fields[date_field.field].widget =  forms.widgets.DateInput(attrs={'type': 'date'})
                if date_field.initial:
                    self.fields[date_field.field].initial = timezone.now()
        else:
           for date_field in date_fields:
                self.form.fields[date_field.field].widget =  forms.widgets.DateInput(attrs={'type': 'date'})
                if date_field.initial:
                    self.form.fields[date_field.field].initial = timezone.now() 






def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
            if not isinstance(result, (list, tuple)):
                    result = [result]
            result = list(os.path.realpath(path) for path in result)
            path=result[0]
    else:
            sUrl = settings.STATIC_URL        # Typically /static/
            sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
            mUrl = settings.MEDIA_URL         # Typically /media/
            mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_static/media/

            if uri.startswith(mUrl):
                    path = os.path.join(mRoot, uri.replace(mUrl, ""))
            elif uri.startswith(sUrl):
                    path = os.path.join(sRoot, uri.replace(sUrl, ""))
            else:
                    return uri

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                    'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path


def render_to_pdf(template_src, context_dict={}):
    template_path = template_src
    context = context_dict
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response, link_callback=link_callback)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

# def render_to_pdf(template_src, context_dict={}):
#     """
#     src: https://github.com/divanov11/django-html-2-pdf/blob/master/htmltopdf/app/views.py

#     https://www.youtube.com/watch?v=5umK8mwmpWM
#     """
#     template = get_template(template_src)
#     html  = template.render(context_dict)
#     result = BytesIO()
#     pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
#     if not pdf.err:
#         return HttpResponse(result.getvalue(), content_type='application/pdf')
#     return None
