from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import login 
from django.contrib.auth.models import User
from django.http import JsonResponse
# Create your views here.

class Register(View):
    def get(self, request):
        form = RegisterForm()
        return render(request, "registration/register.html", {"form":form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # using django builtin sesesion to enable user login automatically after the sighn up successfuly
            login(request, user)
            messages.success(request, 'your account has been created successfully you are  now log in')
            return redirect(reverse_lazy("home:home"))
        return render(request, "registration/register.html", {"form":form})

def validate_username(request):
    user_name = request.POST.get('username' , None)
    data = {
        'is_taken' : User.objects.filter(username__iexact=user_name).exists()
    }
    return JsonResponse(data)


def my_custom_page_not_found_view(request, exception):
    return render(request, 'home/404.html')