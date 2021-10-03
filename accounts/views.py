from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from django.contrib.auth.forms import UserCreationForm
from accounts.models import Account
from accounts.forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# Create your views here.


def register_view(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():

                form.save()
                response = {'status': True}
                return JsonResponse(json.dumps(response), content_type="application/json",safe=False)
            else:
                response = {'status': False}
                return JsonResponse(json.dumps(response), content_type="application/json",safe=False)

        return render(request, 'accounts/authenticate.html', context)
    return redirect('home')



def login_view(request):
    if not request.user.is_authenticated:
        context = {}
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                response = {'status': True}
                return JsonResponse(json.dumps(response), content_type="application/json",safe=False)

            response = {'status': False}
            return JsonResponse(json.dumps(response), content_type="application/json",safe=False)

        return render(request, 'accounts/authenticate.html', context)
    return redirect('home')

def logout_view(request):
    logout(request)
    return redirect('login')
