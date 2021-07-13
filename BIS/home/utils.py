from django.utils import timezone
from django import forms
from typing import List


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