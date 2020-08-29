from django.urls import path
from . import views

app_name = "new_partner_admission"
urlpatterns = [
    path("" , views.NewPartnerAdmission.as_view(), name ="new_partner_admission")
]