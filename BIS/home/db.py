from django.db.models import  DateField, Func

class CurrentDate(Func):
    template = "CURRENT_DATE"
    output_field = DateField()