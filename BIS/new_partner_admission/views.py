from django.shortcuts import render
from django.views import View
# Create your views here.

class NewPartnerAdmission(View):
    def get(self , request):
        return render(request , "new_partner_admission/index.html")
